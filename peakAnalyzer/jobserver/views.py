import basespace
import datetime, os, sys,  time,traceback
from django.utils import simplejson
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.http import HttpResponse
from BaseSpacePy.api.BaseSpaceAPI import BaseSpaceAPI
from django.http import Http404
from django.shortcuts import redirect
from basespace.models import Project,User,AppResult,Sample,File
from jobserver.models import Job
from django.utils import timezone
import basespace.settings
import peakAnalyzer.settings
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from jobserver.tasks import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth import authenticate, login

# Create your views here.
def listjob(request,user_id):
    session_id =4 #debug
    u=get_object_or_404(User, pk=user_id)
    css=dict()
    css["Downloading"]=""
    css["Data_Ready"]="info"
    css["PeakCalling"]="info"
    css["Processing"]="warning"
    css["Completed"]="success"
    css["Error"]="error"
    return render_to_response('jobserver/joblist.html', {'jobs_list':u.job_set.all(),'css':css, 'session_id':session_id})

def get_immediate_subdirectories(dir):
    return [name for name in os.listdir(dir)
            if os.path.isdir(os.path.join(dir, name))]

def CENTDIST_result(dir1):
    myTab=os.path.basename(dir1)
#    html_str="<script type='text/javascript'>$('#tab__"+myTab+"').click(function () {"
#    html_str+= "$(this).load('http://genome.ddns.comp.nus.edu.sg/~chipseq/webseqtools2/TASKS/Motif_Enrichment/viewresult.php?rundir="+dir1+"');"
#    #html_str="<script type='text/javascript'>window.alert('hello');</script>"
#    html_str+="});</script>\n"
#    html_str="<div class='tab-pane' id='"+os.path.basename(dir1)+"""'><iframe id="iFrame1" name="iFrame1" 
#    width="100%" onload="this.height=iFrame1.document.body.scrollHeight" frameborder="0" 
#    src='http://genome.ddns.comp.nus.edu.sg/~sokemay/Motif_Enrichment/viewresult_peakAnalyzer.php?rundir="""+dir1+"'></iframe></div>\n"
    html_str="<div class='tab-pane' id='"+os.path.basename(dir1)+"'><object data='/~sokemay/Motif_Enrichment/viewresult_peakAnalyzer.php?rundir="+dir1+"' type='text/html'></object></div>\n"

    return html_str

def GREAT_result(dir1):
    myTab=os.path.basename(dir1)
    html_str="<div class='tab-pane' id='"+os.path.basename(dir1)+"'>"+'<script> $(document).ready( function () {\
$(\'.table.table-striped.table-bordered.table-condensed\').dataTable({\
            "aaSorting": [[ 1, "asc" ], [7,"asc"]],\
            "sDom": "<\'row\'<\'span6\'l><\'span6\'f>r>t<\'row\'<\'span6\'i><\'span6\'p>>",\
            "sPaginationType": "bootstrap",\
            "aoColumns": [{ "sType": \'string\' },{ "sType": \'numeric\' },{ "sType": \'numeric\' },{ "sType": \'numeric\' },{ "sType": \'numeric\' },{ "sType": \'numeric\' },{ "sType": \'percent\' },{ "sType": \'numeric\' },{ "sType": \'numeric\' },{ "sType": \'numeric\' },{ "sType": \'numeric\' },{ "sType": \'numeric\' },{ "sType": \'numeric\' },{ "sType": \'percent\' },]\
           }); } );</script>'
    
    htmlfile=glob.glob(dir1+"/*.html")
    if htmlfile:
        table=open(htmlfile[0],'r').read()
    else:
        table=''
    #DEBUG URL
    try:
        fileurl=glob.glob(dir1+"/*.txt")[0]  #renamed great output to xls filetype
        fileurl=fileurl.replace("/home/sokemay/basespace/basespace-ui/basespace-ui/peakAnalyzer/", "../../../")
    except:
        fileurl=''
    download_btn='<div style="padding-bottom:20px" id="great_download_btn"><a target="_blank" href="'+fileurl+'"><button class="btn btn-success">Download Peak Gene Associations <span class="icon-download icon-white"></button></span></a></div>'
    html_str=html_str+download_btn+table + '</div>\n'
    return html_str

def denovoMotif_result(dir1):
    myTab=os.path.basename(dir1)
    html_str='<div class="tab-pane" id="'+os.path.basename(dir1)+'">'
     
    filelist=os.listdir(dir1)
    table=''
    for f in filelist:
        if 'html' in f:
            try:
                table=open(dir1 +"/"+f,'r').read()
            except:
                print "file format error"
    pwm_result=dir1.replace("/home/chipseq/basespace/peakAnalyzer/peakAnalyzer/../", "/peakAnalyzer/") + "/SEME_clust.pwm"
    html_button='<a target="_blank" style="padding-bottom:150px" id="download" href="'+pwm_result +'"><button class="btn btn-primary" type="submit">Download PWM Result <span class="icon-download icon-white"></span></button></a>'
    
    html_str=html_str+html_button+ table+'</div>\n'
    
    return html_str

def resultfolder_html(dir1):
    html_str="<div class='tab-pane' id='"+os.path.basename(dir1)+"'>"
    #show image first
    types = ('*.jpg', '*.png','*.bmp') 
    files_grabbed = []
    json_file=[]
    for files in types:
        files_grabbed.extend(glob.glob(str(dir1)+"/"+files))
    for fl in files_grabbed:
        weburl=fl.replace(peakAnalyzer.settings.MEDIA_ROOT,"/peakAnalyzer"+peakAnalyzer.settings.MEDIA_URL)
        html_str+="<div><a  href='"+weburl+"' target=_blank><img src='"+weburl+"' width='500'/><br>"+os.path.basename(fl)+"</a></div>"
    #show file download link with accept format
    
    json_file.extend(glob.glob(str(dir1)+"/*.json"))
    for fl in json_file:
        #jsfile=(str(dir1)+"/test1.json").replace(peakAnalyzer.settings.MEDIA_ROOT,"/peakAnalyzer"+peakAnalyzer.settings.MEDIA_URL)
        jsfile=fl.replace(peakAnalyzer.settings.MEDIA_ROOT,"/peakAnalyzer"+peakAnalyzer.settings.MEDIA_URL);
        html_str+="<script type=\"text/javascript\">\n$(document).ready(function() {$.getJSON(\'"+jsfile+"\', function(data) {var chart = new Highcharts.Chart(data);});})\n</script>\n"
        html_str+="<div id=\""+os.path.basename(jsfile).split('.')[0]+"\" style=\"width: 800px\"></div>\n"
    
    html_str+="</div>\n"
    return html_str

def jobinfo_html(job, result_dir):
    toolpath=os.path.join(peakAnalyzer.settings.ROOT_DIR, '../jobserver_regular').replace('\\','/')
    outdir=result_dir+'/job_info/'
    mkpath(outdir)
    job_desc_out=outdir+"jobdescription.html"
    
        #add alt cellline
    try:
        alt_cl=open(result_dir+"/pipeline_result/detected_cl.txt").readline()
    except:
        alt_cl=''


   # os.system("rm " + job_desc_out)
    cmd="python "+toolpath+"/generateJobInfoHtml.py '" + job.jobtitle + "' '" + job.ref_genome+ "' '" + job.cell_line + "' '"+alt_cl +"' '" + job.sampleFiles+ "' '" + job.controlFiles + "' " +result_dir+ " " + job_desc_out + ' '+toolpath
#    cmd="python "+toolpath+"/generateJobInfoHtml.py " + str(job.id) +" "+result_dir+ " " +job_desc_out
    print cmd
    os.system(cmd)
    try:
        job_desc=open(job_desc_out).read()
    except:
        job_desc=''
    html_str="<div class='tab-pane active' id='job_info'>" +job_desc+ "</div>"
    
    
    return html_str
@login_required      
def viewresult(request,job_id):
    job=get_object_or_404(Job, pk=job_id)
    result_dir=peakAnalyzer.settings.MEDIA_ROOT+"/"+job.user.Email+"/"+str(job.id)+"/pipeline_result/"
    result_list=get_immediate_subdirectories(result_dir)
    job_info_html=jobinfo_html(job, str(result_dir)+"../")
    content_html=" "
    for dir1 in result_list:
        if "CENTDIST" in dir1:
            content_html+=CENTDIST_result(str(result_dir)+"/"+str(dir1))
        elif "denovo" in dir1:
            content_html+=denovoMotif_result(str(result_dir)+"/"+str(dir1))

        elif "GREAT" in dir1:
            content_html+=GREAT_result(str(result_dir)+"/"+str(dir1))
        else:
            content_html+=resultfolder_html(str(result_dir)+"/"+str(dir1))
    return render_to_response('jobserver/viewresult.html', {'result_list':result_list,'job':job,'content_html':content_html,'job_info':job_info_html})