#!/usr/bin/python3

import os, sys
import json
import pickle
from tqdm import tqdm

import traceback

from Bio import SeqIO
from antismash_to_database_functions import buildCluster, getPKSNRPSAccessions

sys.path.insert(0, '/clusterCAD')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "clusterCAD.settings")
import django
django.setup()
import pks.models

# Identify valid type I modular PKSs and NRPS from MIBiG files
print('Analyzing contents of MIBiG database.')
mibigpath = './data/mibig/raw/mibig_json_4.0'
antismashpath = './data/antismash/raw' 
print("Processing cluster types: Polyketide, NRP")
mibigaccessions = getPKSNRPSAccessions(mibigpath)
print('\n')

# Reset database (comment out if you want to generate individual clusters without wiping the database)
print('Resetting ClusterCAD database.')
[cluster.delete() for cluster in pks.models.Cluster.objects.all()]
print('ClusterCAD database reset.\n')

# Assumes that chemical structures have already been aggregated
allknowncompounds = pickle.load(open('./data/compounds/all_known_products.p', 'rb'))

# If you want a list of all the mibig accessions for clusters to be generated
# print(mibigaccessions)

#for accession in ['BGC0000031']: # Debug with Borreledin
mibig_count = len(mibigaccessions)
print(mibigaccessions)
for i, accession in enumerate(mibigaccessions[:10]):
    print(f"\r{accession} : {i}/{mibig_count}", end='', flush=True, file=sys.stderr)
  
    # Use accession number to get paths to MIBiG and antiSMASH files
    mibigfile = os.path.join(mibigpath, accession + '.json')
    clusterfile = os.path.join(antismashpath, accession, accession + '.gbk')
    print("#01", mibigfile)
    print("#01", clusterfile)

    # Read antiSMASH annotations for cluster
    try:
        print("\n#02 " + clusterfile)
        record = SeqIO.read(clusterfile, "genbank")
    
    # If file is missing, we skip the cluster
    except FileNotFoundError:
        print('Missing file: %s' %clusterfile)
        continue

    with open(mibigfile) as f:
        jsondata = json.loads(f.read())
        # Get compound name from MIBiG entry
        clusterproduct = ', '.join([x['name'] for x in jsondata['compounds']])
        gbkAccession = jsondata['loci'][0]['accession']
        mibigVersion = str(jsondata['version'])

    # Get compound information
    try:
        compound = allknowncompounds[accession]
    
    # If compound is missing, we skip the cluster
    except KeyError:
        print('#03 Missing compound %s: %s.' %(accession, clusterproduct))
        continue
    # some clusters like 416 has a space at front of smiles string
    knownproductsmiles = compound[0][0].strip() 
    
    knownproductsource = compound[1]
    
    # Enter information in ClusterCAD database
    # FOR DEBUGGING INDIVIDUAL CLUSTERS: comment out try/except to not ignore problematic clusters
    try:
            # build cluster if not already exists (for testing pipeline purposes)
            #print(pks.models.Cluster.objects.filter(mibigAccession=str(accession)+".1"))
        if len(pks.models.Cluster.objects.filter(mibigAccession=str(accession)+"."+mibigVersion)) == 0:
            cluster = pks.models.Cluster(
                genbankAccession=gbkAccession, \
                mibigAccession=record.id, \
                mibigVersion=mibigVersion, \
                description=clusterproduct, \
                sequence=record.seq,
                knownProductSmiles=knownproductsmiles,
                knownProductSource=knownproductsource
                )
            cluster.save()
            # Processes subunits and modules belonging to cluster
            buildCluster(cluster, record)
            print('#04 Processed cluster %s: %s.' %(record.id, clusterproduct))
            cluster.computeProduct()
            print('#05 Pregenerated cluster products.')
        else:
            print("#06 Cluster already exists. Please delete if regeneration desired. ")
    except Exception as e:
        print("#07", e)
        # traceback.print_exc()
        pass

print("\nClusterCAD data successfully loaded. ")