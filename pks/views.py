import re
from django.shortcuts import render
from model_utils.managers import InheritanceManager
from django.http import HttpResponse
from .models import Cluster, Module, Subunit, Domain
from django.http import Http404
from json import dumps
from rdkit import Chem as chem
from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def index(request, show):

    # determine if we will show all or only reviewed PKSs
    if show == 'reviewed':
        showAll = False
    else:
        showAll = True

    try:
        if showAll:
            # get all PKS clusters
            # clusters = Cluster.objects.order_by('description')
            clusters = Cluster.objects.order_by('mibigAccession')
        else:
            # get only manually reviewed PKS clusters
            # clusters = Cluster.objects.filter(reviewed=True).order_by('description')
            clusters = Cluster.objects.filter(reviewed=True).order_by('mibigAccession')
    except Cluster.DoesNotExist:
        raise Http404

    clusterlist = [] 
    for cluster in clusters:
        clusterDict = {
            'clusterObject': cluster,
            'subunitCount': Subunit.objects.filter(cluster=cluster).count(),
            'moduleCount': Module.objects.filter(subunit__cluster=cluster).count(),
        }
        clusterlist.append(clusterDict)

    context={'clusters': clusterlist, 'showAll': showAll}

    return render(request, 'index.html', context)

@ensure_csrf_cookie
def details(request, mibigAccession):
    try:
        cluster=Cluster.objects.get(mibigAccession=mibigAccession)
    except Cluster.DoesNotExist:
        raise Http404

    if 'mark' in request.GET:
        mark = [int(m) for m in request.GET['mark'].split(',')]
    else:
        mark = [] 

    architecture = cluster.architecture()

    # compute MCS percentages
    knownProduct = chem.MolFromSmiles(cluster.knownProductSmiles)
    mcs = chem.MolFromSmarts(cluster.knownProductMCS) 
    knownProductPercent = 100.0 * float(mcs.GetNumAtoms()) / float(knownProduct.GetNumAtoms())
    predictedProduct = architecture[-1][1][-1][0].product.mol()
    predictedProductPercent = 100.0 * float(mcs.GetNumAtoms()) / float(predictedProduct.GetNumAtoms())

    context={
            'cluster': cluster, 
            'architecture': architecture,
            'mark': mark,
            'notips': ('KS', 'ACP', 'PCP'),
            'predictedProductPercent': predictedProductPercent,
            'knownProductPercent': knownProductPercent,
    }

    return render(request, 'details.html', context)

def domainLookup(request):
    if request.is_ajax():
        try:
            domainid = request.GET['domainid']
            domain = Domain.objects.filter(id=int(domainid)).select_subclasses()[0]
            response = {
                'name': '%s subunit %s module %s: %s domain' % (domain.module.subunit.cluster.description, domain.module.subunit.name, domain.module.order, repr(domain)),
                'start': str(domain.start),
                'stop': str(domain.stop),
                'annotations': str(domain),
                'AAsequence': domain.getAminoAcidSequence(),
            }
        except:
            raise Http404
        return HttpResponse(dumps(response), 'text/json')
    else:
        raise Http404

def subunitLookup(request):
    if request.is_ajax():
        try:
            subunitid = request.GET['subunitid']
            subunit = Subunit.objects.get(id=int(subunitid))
            response = {
                'name': '%s subunit %s' % (subunit.cluster.description, subunit.name),
                'id': str(subunit.id),
                'start': str(subunit.start),
                'stop': str(subunit.stop),
                'genbankAccession': subunit.genbankAccession,
                'genbankAccessionShort': re.sub("\.\d+$", "", subunit.genbankAccession),
                'AAsequence': subunit.getAminoAcidSequence(),
                'DNAsequence': subunit.getNucleotideSequence(),
                'ss': subunit.ss8,
                'acc': subunit.acc20, 
            }
            if subunit.accPlotFile != '':
                response['accplot'] = subunit.accPlotFile.url
            else:
                response['accplot'] = ''
            if subunit.ssPlotFile != '':
                response['ssplot'] = subunit.ssPlotFile.url
            else:
                response['ssplot'] = ''
        except:
            raise Http404
        return HttpResponse(dumps(response), 'text/json')
    else:
        raise Http404

