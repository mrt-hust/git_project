{
    'name': 'Github Project',
    'sequence': 10,
    'summary': 'Connect to github, synchronize and notify',
    'version': '1.0',
    'description': "",
    'depends': ['project', 'web'],
    'data': [
        'views/project_views.xml',
        'views/config.xml',
        'views/header.xml'
    ],
    'installable': True,
    'application': True,
}
