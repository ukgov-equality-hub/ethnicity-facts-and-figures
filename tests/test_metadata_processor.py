import pytest
import csv
from tempfile import TemporaryDirectory

from application.cms.data_utils import MetadataProcessor, DataProcessor
from application.cms.file_service import FileService


def test_data_processor_does_copy_all_files_for_page(app, stub_measure_page):

    file_service = FileService()
    file_service.init_app(app)

    '''
    Given
    two viable uploaded files
    '''
    file_system = file_service.page_system(stub_measure_page)

    write_temporary_csv_to_file_service(file_system=file_system, file_path='source/input_01.csv')
    write_temporary_csv_to_file_service(file_system=file_system, file_path='source/input_01.xls')

    '''
    When
    we run the data processor
    '''
    processor = DataProcessor()
    processor.file_service = file_service
    processor.process_files(page=stub_measure_page)

    '''
    Then
    the two files are copied across
    '''

    assert len(file_system.list_files('source')) == 2
    assert len(file_system.list_files('data')) == 2


def test_data_processor_does_remove_files_from_data_folder(app, stub_measure_page):

    file_service = FileService()
    file_service.init_app(app)

    '''
    Given
    we have uploaded and processed as in the previous test
    '''
    file_system = file_service.page_system(stub_measure_page)
    write_temporary_csv_to_file_service(file_system=file_system, file_path='source/input_01.csv')
    write_temporary_csv_to_file_service(file_system=file_system, file_path='source/input_01.xls')

    processor = DataProcessor()
    processor.file_service = file_service
    processor.process_files(page=stub_measure_page)

    '''
    When
    we delete one file and run the data processor
    '''
    file_system.delete(fs_path='source/input_01.csv')
    processor.process_files(page=stub_measure_page)

    '''
    Then
    only one file will exist in each folder
    '''
    assert len(file_system.list_files('source')) == 1
    assert len(file_system.list_files('data')) == 1


def test_metadata_processor_does_save_to_output_file(app, stub_measure_page):

    '''
    Given
    a temporary setup
    '''
    file_service = FileService()
    file_service.init_app(app)
    file_system = file_service.page_system(stub_measure_page)

    input_path = 'input_02.csv'
    write_temporary_csv_to_file_service(file_system, input_path)
    output_path = 'output_02.csv'

    '''
    When
    we run the processor
    '''
    processor = MetadataProcessor(file_service)
    processor.process_page_level_file(input_path=input_path, output_path=output_path, page=stub_measure_page)

    '''
    Then
    an output file is generated
    '''
    assert output_path in file_system.list_files(fs_path='')


def test_metadata_processor_does_write_input_file_to_output_file(app, stub_measure_page):
    '''
    Given
    a temporary setup with content in the input file
    '''
    file_service = FileService()
    file_service.init_app(app)
    file_system = file_service.page_system(stub_measure_page)

    input_path = 'input_03.csv'
    write_temporary_csv_to_file_service(file_system, input_path)

    output_path = 'output_03.csv'

    '''
    When
    we run the processor
    '''
    processor = MetadataProcessor(file_service)
    processor.process_page_level_file(input_path=input_path, output_path=output_path, page=stub_measure_page)

    '''
    Then
    the output is copied
    '''
    with TemporaryDirectory() as test_dir:
        tmp_file = test_dir + '/tmp.csv'
        file_system.read(fs_path=output_path, local_path=tmp_file)
        cells = read_csv_to_list_of_cells(tmp_file)
        assert 'title_1' in cells
        assert 'title_2' in cells
        assert 'a' in cells
        assert 'b' in cells


def test_metadata_processor_does_write_page_metadata_row_headings_to_output_file(app, stub_measure_page):
    '''
        Given
        a temporary setup with content in the input file
        '''
    file_service = FileService()
    file_service.init_app(app)
    file_system = file_service.page_system(stub_measure_page)

    input_path = 'input_04.csv'
    write_temporary_csv_to_file_service(file_system, input_path)

    output_path = 'output_04.csv'

    '''
    When
    we run the processor
    '''
    processor = MetadataProcessor(file_service)
    processor.process_page_level_file(input_path=input_path, output_path=output_path, page=stub_measure_page)

    '''
    Then
    the output is copied
    '''
    with TemporaryDirectory() as test_dir:
        tmp_file = test_dir + '/tmp.csv'
        file_system.read(fs_path=output_path, local_path=tmp_file)
        rows = read_csv_to_list(tmp_file)
        assert rows[0][0] == 'Title:'
        assert rows[1][0] == 'Time period:'
        assert rows[2][0] == 'Location:'
        assert rows[3][0] == 'Source:'
        assert rows[4][0] == 'Department:'
        assert rows[5][0] == 'Last update:'


def test_metadata_processor_does_write_page_metadata_to_output_file(app, stub_measure_page):
    '''
        Given
        a temporary setup with content in the input file
        '''
    file_service = FileService()
    file_service.init_app(app)
    file_system = file_service.page_system(stub_measure_page)

    input_path = 'input_03.csv'
    write_temporary_csv_to_file_service(file_system, input_path)

    output_path = 'output_03.csv'

    '''
    When
    we run the processor
    '''
    processor = MetadataProcessor(file_service)
    processor.process_page_level_file(input_path=input_path, output_path=output_path, page=stub_measure_page)

    '''
    Then
    the output is copied
    '''
    with TemporaryDirectory() as test_dir:
        tmp_file = test_dir + '/tmp.csv'
        file_system.read(fs_path=output_path, local_path=tmp_file)
        rows = read_csv_to_list(tmp_file)
        assert rows[0][1] == stub_measure_page.title
        assert rows[1][1] == stub_measure_page.time_covered
        assert rows[2][1] == stub_measure_page.geographic_coverage
        assert rows[3][1] == stub_measure_page.source_text
        assert rows[4][1] == stub_measure_page.department_source
        assert rows[5][1] == stub_measure_page.last_update_date


def write_temporary_csv_to_file(file_path):
    with open(file_path, 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['title_1', 'title_2'])
        writer.writerow(['a', 'b'])


def write_temporary_csv_to_file_service(file_system, file_path):
    with TemporaryDirectory() as test_dir:
        write_temporary_csv_to_file(test_dir + '/tmp.tmp')
        file_system.write(test_dir + '/tmp.tmp', file_path)


def read_csv_to_list(file_path):
    with open(file=file_path) as csv_file:
        reader = csv.reader(csv_file)
        return [row for row in reader]


def read_csv_to_list_of_cells(file_path):
    cells = []
    with open(file=file_path) as csv_file:
        reader = csv.reader(csv_file)
        [cells.extend(row) for row in reader]
        return cells
