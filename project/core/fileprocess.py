from shutil import rmtree
from os import path, makedirs

import pandas as pd


def create_dir(file_path):
    makedirs(file_path, mode=0o777, exist_ok=True)


def delete_dir(dir_name):
    if path.exists(dir_name):
        rmtree(dir_name)


def get_data_from_file(file_name):
    if file_name.endswith('.csv'):
        df = pd.read_csv(file_name)
    elif file_name.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(file_name, index_col=None)
    elif file_name.endswith('.tsv'):
        df = pd.read_csv(file_name, sep='\t')
    else:
        return False
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df


def get_project_root(media_root, user_id, project_id):
    return path.join(media_root, str(user_id), str(project_id))


def get_project_dir(media_root, user_id, project_id):
    return path.join(media_root, str(user_id), str(project_id), 'project')


def get_models_dir(media_root, user_id, project_id, model_id):
    return path.join(media_root, str(user_id), str(project_id), 'models', str(model_id))


def get_stats_dir(media_root, user_id, project_id):
    return path.join(media_root, str(user_id), str(project_id), 'stats')


def get_charts_dir(media_root, user_id, project_id):
    return path.join(media_root, str(user_id), str(project_id), 'charts')


def get_profile_picture_dir(media_root, user_id):
    return path.join(media_root, str(user_id), 'picture')


def get_profile_thumbnail_dir(media_root, user_id):
    return path.join(media_root, str(user_id), 'picture', 'thumbnail')


def get_quotes_dir(media_root):
    return path.join(media_root, 'quotes')
