import pysam
from celescope.tools.step import Step, s_common
from collections import defaultdict
import subprocess
import pandas as pd
from celescope.tools import utils


class Count(Step):
    def __init__(self, args, step_name):
        Step.__init__(self, args, step_name)

        self.outdir = args.outdir
        self.sample = args.sample
        self.bam_file = args.bam_file
        self.cells = args.cells


    @utils.add_log
    def count_bam(self):
        rawbam = pysam.AlignmentFile(self.bam_file, "rb")
        header = rawbam.header
        new_bam = pysam.AlignmentFile(
            self.bam_file + ".temp", "wb", header=header)
        dic = defaultdict(list)
        for read in rawbam:
            attr = read.query_name.split('_')
            barcode = attr[0]
            umi = attr[1]
            read.set_tag(tag='CB', value=barcode, value_type='Z')
            read.set_tag(tag='UB', value=umi, value_type='Z')
            if dic[barcode].count(umi) < 1:
                dic[barcode].append(umi)
            new_bam.write(read)
        new_bam.close()
        cmd = f'mv {self.bam_file}.temp {self.bam_file}'
        subprocess.check_call(cmd, shell=True)

        df = pd.DataFrame()
        df['barcode'] = list(dic.keys())
        df['UMI'] = [len(dic[i]) for i in list(dic.keys())]
        df.to_csv(f'{self.outdir}/count.txt', sep='\t', index=False)
        return df


    def cut_off(self):
        df = self.count_bam()
        df_sorted = df.sort_values(by='UMI', ascending=False)

        UMI_num = int(self.cells)
        rank = UMI_num / 100
        rank_UMI = df_sorted.loc[rank, 'UMI']
        UMI_min = int(rank_UMI / 10)

        df_umi_filtered = df_sorted[df_sorted.UMI >= UMI_min]

        barcodes = df_umi_filtered.barcode.tolist()

        return barcodes


    @utils.add_log
    def filter_bam(self):
        barcodes = self.cut_off()
        bam = pysam.AlignmentFile(self.bam_file, "rb")
        header = bam.header
        newbam = pysam.AlignmentFile(f'{self.outdir}/{self.sample}_toassemble.bam', 'wb', header=header)
        for read in bam:
            attr = read.query_name.split('_')
            barcode = attr[0]
            if barcode in barcodes:
                newbam.write(read)

    @utils.add_log
    def run(self):
        self.filter_bam()

@utils.add_log
def count(args):
    step_name = 'count'
    count_obj = Count(args, step_name)
    count_obj.run()


def get_opts_count(parser, sub_program):
    if sub_program:
        parser = s_common(parser)
        parser.add_argument('--bam_file', help='BAM file form STAR step', required=True)
    parser.add_argument('--cells', help='expected cell number', default=3000)


            

