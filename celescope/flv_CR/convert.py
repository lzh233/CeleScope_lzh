import os
import subprocess

import pysam
import pandas as pd
from xopen import xopen

from celescope.tools import utils
from celescope.tools.step import Step, s_common


UMI_10X_LEN = 10
TSO = "TTTCTTATATGGG"
WHITELIST_10X_PATH = "/lib/python/cellranger/barcodes/737K-august-2016.txt"

class Convert(Step):
    """
    Features

    - Convert barcodes and UMI to 10X format.

    Output        
    - `02.convert/barcode_correspond.txt` Recording barcodes correspondence.

    - `02.convert/{sample}_S1_L001_R1_001.fastq.gz` New R1 reads as cellranger input.

    - `02.convert/{sample}_S1_L001_R2_001.fastq.gz` New R2 reads as cellranger input.
    """

    def __init__(self, args, display_title=None):
        Step.__init__(self, args, display_title=display_title)
        self.fq2 = args.fq2

        self.whitelist_10X_file = os.path.dirname(args.soft_path) + WHITELIST_10X_PATH
        self.whitelist_10X_fh = xopen(self.whitelist_10X_file, 'r')
        self.sgr_tenX = {}

        # out
        self.out_fq1_file = f'{self.outdir}/{self.sample}_S1_L001_R1_001.fastq.gz'
        self.out_fq2_file = f'{self.outdir}/{self.sample}_S1_L001_R2_001.fastq.gz'
        self.barcode_convert_json = f'{self.outdir}/barcode_convert.json'

    @utils.add_log
    def write_fq1(self):      
        out_fq1 = xopen(self.out_fq1_file, 'w')

        with pysam.FastxFile(self.fq2) as fq2_fh:
            for entry in fq2_fh:
                name = entry.name
                attrs = name.split('_')
                sgr_barcode, sgr_umi = attrs[0], attrs[1]
                new_seq1, new_qual1 = self.convert_seq(sgr_barcode, sgr_umi)
                out_fq1.write(f'@{name}\n{new_seq1}\n+\n{new_qual1}\n')

        out_fq1.close()

    @utils.add_log
    def gzip_fq2(self):
        cmd = f'gzip -c {self.fq2} > {self.out_fq2_file}'
        subprocess.check_call(cmd, shell=True)
   
    def convert_seq(self, barcode_sgr, umi_sgr):
        """
        Convert sgr barcode to 10X barcode; change length of sgr UMI to UMI_10X_LEN

        Args:
            barcode_sgr: str
            umi_sgr: str
        Returns:
            new_seq1: str
            new_qual1: str
        """

        if barcode_sgr in self.sgr_tenX:
            barcode_10X = self.sgr_tenX[barcode_sgr]
        else:
            # new barcode from whitelist
            barcode_10X = self.whitelist_10X_fh.readline().strip()
            self.sgr_tenX[barcode_sgr] = barcode_10X

        umi_len_sgr = len(umi_sgr)
        if umi_len_sgr > UMI_10X_LEN:
            umi_10X = umi_sgr[:UMI_10X_LEN]
        elif umi_len_sgr < UMI_10X_LEN:
            umi_10X = umi_sgr + 'C' * (UMI_10X_LEN - umi_len_sgr)
        else:
            umi_10X = umi_sgr

        new_seq1 = barcode_10X + umi_10X + TSO
        new_qual1 = 'F' * len(new_seq1)

        return new_seq1, new_qual1

    @utils.add_log
    def dump_tenX_sgr_barcode_json(self):
        self.tenX_sgr = {}
        for sgr, tenX in self.sgr_tenX.items():
            self.tenX_sgr[tenX] = sgr

        utils.dump_dict_to_json(self.tenX_sgr, self.barcode_convert_json)

    def run(self):
        self.write_fq1()
        self.gzip_fq2()
        self.dump_tenX_sgr_barcode_json()

def convert(args):
    step_name = 'convert'
    with Convert(args, step_name) as runner:
        runner.run()


def get_opts_convert(parser, sub_program):
    parser.add_argument('--soft_path', help='soft path for cellranger', required=True)
    if sub_program:
        s_common(parser)
        parser.add_argument('--fq2', help='R2 read file', required=True)
    return parser
