from collections import defaultdict
import pysam
import gzip
import numpy as np
import subprocess
import os
from xopen import xopen
from celescope.tools.utils import genDict, log, fastq_line


@log
def sort_fastq(fq, fq_tmp_file):
    cmd = (
        f'zcat {fq} | paste - - - - | sort -k1,1 -t " " | tr "\t" "\n" > {fq_tmp_file};'
    )
    subprocess.check_call(cmd, shell=True)


@log
def sorted_dumb_consensus(fq, outfile, threshold):
    '''
    read in name sorted fastq, output (barcode,umi) consensus fastq
    '''
    curr_combine = ""
    read_list = []
    n = 0
    out_h = xopen(outfile, 'w')

    with pysam.FastxFile(fq) as fh:
        for entry in fh:
            attr = entry.name.split('_')
            barcode = attr[0]
            umi = attr[1]
            combine = [barcode,umi]
            if combine != curr_combine:
                # first
                if curr_combine == "":
                    curr_combine = combine
                    read_list.append([entry.sequence,entry.quality])
                    continue
                consensus, consensus_qual = dumb_consensus(read_list, threshold=threshold, ambiguous="N")
                n += 1
                prefix = "_".join(curr_combine)
                read_name = f'{prefix}_{n}'
                out_h.write(fastq_line(read_name,consensus,consensus_qual))
                if n % 10000 == 0:
                    sorted_dumb_consensus.logger.info(f'{n} UMI done.')
                read_list = []
                curr_combine = combine
            read_list.append([entry.sequence,entry.quality])
    #last
    consensus, consensus_qual = dumb_consensus(read_list, threshold=0.5, ambiguous="N")  
    n += 1
    read_name = f'{barcode}_{umi}_{n}'
    out_h.write(fastq_line(read_name,consensus,consensus_qual))

    out_h.close()
    return n


@log
def wrap_consensus(fq, outdir, sample, threshold):
    fq_tmp_file = f'{outdir}/{sample}_sorted.fq.tmp'
    sort_fastq(fq_tmp_file)
    outfile = f'{outdir}/{sample}_consensus.fq'
    n = sorted_dumb_consensus(fq=fq_tmp_file, outfile=outfile, threshold=threshold)
    return outfile, n



def dumb_consensus(read_list, threshold=0.5, ambiguous='N', default_qual='F'):
    '''
    This is similar to biopython dumb_consensus.
    It will just go through the sequence residue by residue and count up the number of each type
    of residue (ie. A or G or T or C for DNA) in all sequences in the
    alignment. If the percentage of the most common residue type is
    greater then the passed threshold, then we will add that residue type,
    otherwise an ambiguous character will be added.
    elements of read_list: [entry.sequence,entry.quality]
    '''

    con_len = get_read_length(read_list, threshold=0.5)
    consensus = ""
    consensus_qual = ""
    for n in range(con_len):
        atom_dict = defaultdict(int)
        quality_dict = defaultdict(int)
        num_atoms = 0
        for read in read_list:
            # make sure we haven't run past the end of any sequences
            # if they are of different lengths
            sequence = read[0]
            quality = read[1]
            if n < len(sequence):
                atom = sequence[n]
                atom_dict[atom] += 1
                num_atoms = num_atoms + 1

                base_qual = quality[n]
                quality_dict[base_qual] += 1

        consensus_atom = ambiguous
        for atom in atom_dict:
            if atom_dict[atom] >= num_atoms * threshold:
                consensus_atom = atom
                break
        consensus += consensus_atom

        max_freq_qual = 0
        consensus_base_qual = default_qual
        for base_qual in quality_dict:
            if quality_dict[base_qual] > max_freq_qual:
                max_freq_qual = quality_dict[base_qual]
                consensus_base_qual = base_qual

        consensus_qual += consensus_base_qual
    return consensus, consensus_qual


def get_read_length(read_list, threshold=0.5):
    '''
    compute read_length from read_list. 
    length = max length with read fraction >= threshold
    elements of read_list: [entry.sequence,entry.quality]
    '''
    
    n_read = len(read_list)
    length_dict = defaultdict(int)
    for read in read_list:
        length = len(read[0])
        length_dict[length] += 1
    for length in length_dict:
        length_dict[length] = length_dict[length] / n_read

    fraction = 0
    for length in sorted(length_dict.keys(),reverse=True):
        fraction += length_dict[length]
        if fraction >= threshold:
            return length


def consensus(args):
    sample = args.sample
    outdir = args.outdir
    assay = args.assay
    fq = args.fq
    threshold = float(args.threshold)
    not_consensus = args.not_consensus

    if not os.path.exists(outdir):
        os.system('mkdir -p %s' % outdir)

    wrap_consensus(fq, outdir, sample, threshold)

    



def get_opts_mapping_vdj(parser, sub_program):
    parser.add_argument("--threshold", help='valid base threshold', default=0.5)
    parser.add_argument("--not_consensus", action='store_true', help="do not perform UMI consensus, use read instead")
    if sub_program:
        parser.add_argument('--outdir', help='output dir', required=True)
        parser.add_argument('--sample', help='sample name', required=True)
        parser.add_argument("--fq", required=True)
        parser.add_argument('--assay', help='assay', required=True)