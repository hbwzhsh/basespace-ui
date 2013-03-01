import datetime, os, sys,  time
from django.utils import simplejson
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template.context import RequestContext
from django.http import  *
from django.core.files.uploadedfile import UploadedFile
from django.http import Http404
from regular.models import *
from jobserver_regular.models import RegularJob
from django.utils import timezone
import peakAnalyzer.settings
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from jobserver_regular.tasks import *
from django import forms
from peakAnalyzer.settings import MEDIA_ROOT
import json
from django.utils import simplejson
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout,authenticate, login
from basespace.UploadFileHandler import handle_uploaded_file
from django.contrib.auth.models import User


FileTypes={'Extensions':'bam,vcf,fastq,gz,bed,peak'}

@login_required
def hello(request):
    return HttpResponse("hello")
    
@login_required
def listUploadedFiles(request):
    
    user        = User.objects.get(username=request.user.username) 
    outdir=peakAnalyzer.settings.MEDIA_ROOT+"/"+user.email+"/"
    
    tmpdir=outdir+"tmp/"
    os.system("mkdir " + tmpdir)
    tmp=tmpdir+"uploadedFiles.tmp.txt"
    listCmd="find " + outdir + " -maxdepth 1 -type f  > " +tmp
    os.system(listCmd)
    tmplist= open(tmp, "r")
    uploadedfiles=list()
    for line in tmplist:
        line = line.strip()
        tmpline=line.split("/")
        uploadedfiles.append(tmpline[len(tmpline)-1])
    
    os.system("rm -r " + tmp )
    
    sam = list()
    bam=list()
    bed=list()
    fasta=list()
    fastq=list()    
    
    for f in sorted(uploadedfiles):
        if ".sam" in f:
            sam.append(f)
        if ".bam" in f:
            bam.append(f)
        if ".bed" in f:
            bed.append(f)
        if ".fasta" in f:
            fasta.append(f)
        if ".fastq" in f:
            fastq.append(f)
    
    output={'sam':sam, 'bam':bam, 'bed':bed, 'fasta': fasta,'fastq':fastq}
    
    return HttpResponse(json.dumps(output), content_type='application/json')        
    

@login_required
@csrf_exempt
def uploadFiles(request):
       
    user        = User.objects.get(username=request.user.username)
    outdir=peakAnalyzer.settings.MEDIA_ROOT+"/"+user.email+"/"
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    
    if request.method == 'POST':
       filename=handle_uploaded_file(request.FILES['files[]'], outdir)
       err=""
       path=outdir+filename
       prop = [{'name':filename, 'type':"", 'error': err, 'path': path}]
       response_dict={"files":prop}
       return HttpResponse(json.dumps(response_dict), content_type='application/json')    
    
       
@login_required
def listProject(request):
    projects_list=list()
    name=request.user.username
    user        = User.objects.get(username=name)
    projects = UserProject.objects.filter(owner=user)
    if len(projects)==0:
        projectTitle=user.username+"'s Project"
        proj=UserProject(ProjectId=user.id,Name=projectTitle,owner=user)
        proj.save()
    else:
        proj=projects[0]
            
    projects_list.append(proj)   
        
    return render_to_response('regular/index.html', {'user': user,'projects_list':projects_list})


@login_required
@csrf_exempt
def submitJob(request):
 
    user        = User.objects.get(username=request.user.username)
    samplefids=list()
    controlfids=list()
    cell_line=""
    ref_genome=""
    jobtitle=""
    for postid,postv in request.POST.iteritems():
        if "ctrl" in postid:
            for fid in postv.split(','):    #fid is int if from basespace
                if fid=="":
                    continue
                controlfids.append(fid)
        elif "sample" in postid:
            for fid in postv.split(','):
                if fid=="":
                    continue
                samplefids.append(fid)
        elif "Title" in postid:
            jobtitle=postv
        elif "Genome" in postid:
            ref_genome=postv
        elif "Cell" in postid:
            cell_line=postv
    outdir=peakAnalyzer.settings.MEDIA_ROOT+"/"+user.email+"/"
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    samplefiles=""
    controlfiles=""
    
    myjob=user.regularjob_set.create(status="Data_Ready",ref_genome=ref_genome,cell_line=cell_line,jobtitle=jobtitle,sampleFiles=samplefiles,controlFiles=controlfiles,submitDate=timezone.now())
    
    PeakCalling_Processing.delay(samplefids,controlfids,outdir,myjob.id,user.email)
    return HttpResponse(simplejson.dumps({myjob.id:myjob.jobtitle}), mimetype="application/json");

def rerunJobs(jobs, outdir, useremail):
    if jobs:
        for jid in jobs:
            myjob=RegularJob.objects.get(pk=jid)
            myjob.status="Data_Ready"
            myjob.save()
            
            PeakCalling_Processing.delay(myjob.sampleFiles,myjob.controlFiles,outdir,myjob.id, useremail)
    
                        
def deleteJobs(jobs):
    if jobs:
        for jid in jobs:
            myjob=RegularJob.objects.get(pk=jid)
            print "deleting:",myjob
            myjob.delete()

@csrf_exempt
def jobManagement(request):
    user        = User.objects.get(username=request.user.username)
    outdir=peakAnalyzer.settings.MEDIA_ROOT+"/"+user.email+"/"
    
    jobs_selected=request.POST.getlist('job')
    
    if 'delete' in request.POST:
        deleteJobs(jobs_selected)
        return HttpResponse("Successfully Deleted!")
    elif 'rerun' in request.POST:
        rerunJobs(jobs_selected, outdir, user.email)
        return HttpResponse("Reprocessing job...")


