import numpy as np

from celescope.__init__ import HELP_DICT
from celescope.tools.step import Step, s_common
from celescope.tools import utils
from celescope.tools.count import Count


def get_opts_count_tag(parser, sub_program):
    if sub_program:
        parser.add_argument("--read_count_file", help="Tag read count file.", required=True)
        parser.add_argument("--match_dir", help=HELP_DICT['match_dir'])
        parser.add_argument("--matrix_dir", help=HELP_DICT['matrix_dir'])
        parser.add_argument("--tsne_file", help=HELP_DICT['tsne_file'])
        s_common(parser)


def count_tag(args):

    with Count(args) as runner:
        runner.run()


class Count(Step):
    """
    ## Features

    ## Output

    - `{sample}_umi_tag.tsv` 

    - `{sample}_tsne_tag.tsv` it is `{sample}_umi_tag.tsv` with t-SNE coordinates, gene_counts and cluster infomation
    """

    def __init__(self, args, display_title=None):
        Step.__init__(self, args, display_title=display_title)
        self.read_count_file = args.read_count_file
        self.total_corrected_umi = 0

        # read
        self.df_read_count = pd.read_csv(self.read_count_file, sep="\t", index_col=0)

        if utils.check_arg_not_none(args, 'match_dir'):
            match_dict = utils.parse_match_dir(args.match_dir)
            self.match_barcode = match_dict['match_barcode']
            self.n_match_barcode = match_dict['n_match_barcode']
            self.tsne_file = match_dict['tsne_coord']
            self.matrix_dir = match_dict['matrix_dir']
        elif utils.check_arg_not_none(args, 'matrix_dir'):
            self.match_barcode, self.n_match_barcode = utils.get_barcode_from_matrix_dir(args.matrix_dir)
            self.tsne_file = args.tsne_file
            self.matrix_dir = args.matrix_dir
        else:
            raise ValueError("--match_dir or --matrix_dir is required.")

        # init
        self.no_noise = False

        # out files
        self.UMI_tag_file = f'{self.outdir}/{self.sample}_umi_tag.tsv'
        self.tsne_tag_file = f'{self.outdir}/{self.sample}_tsne_tag.tsv'
        self.corrected_read_count_file = f'{self.out_prefix}_corrected_read_count.json'

    def correct_umi(self):
        for barcode in self.count_dict:
            for ref in self.count_dict[barcode]:
                self.raw_umi += len(self.count_dict[barcode][ref])
                n_corrected_umi, _n_corrected_read = Count.correct_umi(self.count_dict[barcode][ref])
                if self.debug:
                    print(f'{barcode} {ref} {n_corrected_umi}')
                self.total_corrected_umi += n_corrected_umi

    def add_correct_umi_metrics(self):
        self.add_metric(
            name='Number of Raw UMI',
            value=self.raw_umi,
            help_info='number of total raw UMI',
        )

        self.add_metric(
            name='Number of Corrected UMI',
            value=self.total_corrected_umi,
            total=self.raw_umi,
            help_info='correct sequencing errors in the UMI sequences ',
        )

    def write_corrected_read_count_file(self):
        with open(self.corrected_read_count_file, 'w') as fp:
            json.dump(self.read_count_dict, fp, indent=4)

    @utils.add_log
    def run(self):
        self.add_metric(
            name='Median UMI per Cell',
            value=umi_median,
            help_info="Median UMI per scRNA-Seq cell barcode"
        )

        self.add_metric(
            name='Mean UMI per Cell',
            value=umi_mean,
            help_info="Mean UMI per scRNA-Seq cell barcode"
        )
