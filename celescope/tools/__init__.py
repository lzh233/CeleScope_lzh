# barcode
PATTERN_DICT = {
    'auto': None,
    'v0': 'C12U8T18',
    'v1.0': 'C8L16C8L16C8U8T18',
    'v1.1': 'C8L16C8L16C8L1U8T18',
    'v1.2': 'C8L16C8L16C8U12T18',
    'v1.3': 'C8L16C8L16C8L1U12T18',
    'v1.4': 'C8L16C8L16C8L1U12T18',
    'v2.0': 'C9L16C9L16C9L1U12T18',
    # flv_rna is actually U9L16, but the last 10 bases can not be sequenced accurately.
    'flv_rna': 'C8L16C8L16C8U9L6',
    'flv' : 'U9C8L16C8L16C8',
    'customized': None,
}


# count
RAW_MATRIX_DIR_SUFFIX = ['raw_feature_bc_matrix', 'all_matrix']
FILTERED_MATRIX_DIR_SUFFIX = ['filtered_feature_bc_matrix', 'matrix_10X']
MATRIX_FILE_NAME = 'matrix.mtx'
FEATURE_FILE_NAME = 'genes.tsv'
BARCODE_FILE_NAME = 'barcodes.tsv'

# mkref
GENOME_CONFIG = 'celescope_genome.config'
