from celescope.tools import utils, matrix
from celescope.tools.__init__ import FILTERED_MATRIX_DIR_SUFFIX


def get_barcodes_from_matrix_dir(matrix_dir):
    """
    Use matrix.get_barcodes_from_matrix_dir;
    This function is used to avoid importing celescope.tools.matrix.
    """
    return matrix.get_barcodes_from_matrix_dir(matrix_dir)

def get_matrix_dir_from_args(args):
    if utils.check_arg_not_none(args, 'match_dir'):
        matrix_dir = MatchDirParser(args.match_dir).matrix_dir
    elif utils.check_arg_not_none(args, 'matrix_dir'):
        matrix_dir = args.matrix_dir
    else:
        raise ValueError("--match_dir or --matrix_dir is required.")

    return matrix_dir

def get_barcodes_from_args(args):
    matrix_dir = get_matrix_dir_from_args(args)
    return get_barcodes_from_matrix_dir(matrix_dir)
        

class MatchDirParser:
    def __init__(self, match_dir):
        self.match_dir = match_dir

        self.matrix_dir = self.get_matrix_dir()
        self.barcodes = matrix.get_barcodes_from_matrix_dir(self.matrix_dir)

        self.optional_files = {
            'tsne_file': [f'{self.match_dir}/*analysis*/*tsne_coord.tsv'],
            'markers_file': [f'{self.match_dir}/*analysis*/*markers.tsv'],
            'h5ad_file': [f'{self.match_dir}/*analysis*/*.h5ad'],
        }
        self.set_optional_files()

    @utils.add_log
    def get_matrix_dir(self):
        """
        Returns:
            matrix_dir: str
        """
        matrix_dir_pattern_list = []
        for matrix_dir_suffix in FILTERED_MATRIX_DIR_SUFFIX:
            matrix_dir_pattern_list.append(f"{self.match_dir}/*count/*{matrix_dir_suffix}")
    
        matrix_dir = utils.glob_file(matrix_dir_pattern_list)

        return matrix_dir

    @utils.add_log
    def set_optional_files(self):
        """
        """
        for file_key, file_pattern in self.optional_files.items():
            try:
                match_file = utils.glob_file(file_pattern)
            except FileNotFoundError:
                self.set_optional_files.logger.warning(f"No {file_key} found in {self.match_dir}")
            else:
                setattr(self, file_key, match_file)



