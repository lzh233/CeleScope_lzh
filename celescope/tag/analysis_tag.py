import pandas as pd
import math
import plotly
import plotly.express as px
from collections import defaultdict
from celescope.snp.analysis_snp import Analysis_variant

import celescope.tools.utils as utils
from celescope.tools.analysis_mixin import AnalysisMixin
from celescope.tools.step import s_common
from celescope.tools.plotly_plot import Tsne_plot


class Analysis_tag(AnalysisMixin):
    """
    Features
    - Combine scRNA-Seq clustering infromation with tag assignment.
    """

    def __init__(self, args,display_title=None):
        super().__init__(args, display_title)
        self.tsne_tag_file = args.tsne_tag_file
        self.df_tsne_tag = pd.read_csv(self.tsne_tag_file, sep='\t')

    def add_help(self):
        self.add_help_content(
            name='Marker Genes by Cluster',
            content='differential expression analysis based on the non-parameteric Wilcoxon rank sum test'
        )
        self.add_help_content(
            name='avg_log2FC',
            content='log fold-change of the average expression between the cluster and the rest of the sample'
        )
        self.add_help_content(
            name='pct.1',
            content='The percentage of cells where the gene is detected in the cluster'
        )
        self.add_help_content(
            name='pct.2',
            content='The percentage of cells where the gene is detected in the rest of the sample'
        )
        self.add_help_content(
            name='p_val_adj',
            content='Adjusted p-value, based on bonferroni correction using all genes in the dataset'
        )

    def run(self):

        self.add_help()

        tsne_cluster = Tsne_plot(self.df_tsne, 'cluster').get_plotly_div()
        self.add_data(tsne_cluster=tsne_cluster)

        tsne_tag = Tsne_plot(self.df_tsne_tag, 'tag').get_plotly_div()
        self.add_data(tsne_tag=tsne_tag)



def get_opts_analysis_tag(parser, sub_program):
    if sub_program:
        parser.add_argument('--tsne_tag_file', help='`{sample}_tsne_tag.tsv` from count_tag. ', required=True)
        parser.add_argument("--match_dir", help="Match celescope scRNA-Seq directory. ")
        parser.add_argument("--tsne_file", help="t-SNE coord file.")
        parser = s_common(parser)


@utils.add_log
def analysis_tag(args):
    with Analysis_tag(args,display_title="Analysis") as runner:
        runner.run()
