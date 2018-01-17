{
    'name': 'Github Project',
    'sequence': 10,
    'summary': 'Connect to github, synchronize and notify',
    'version': '1.0',
    'description': "",
    'depends': ['project', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/templates.xml',
        'views/project_views.xml',
        'views/config.xml',
        'views/header.xml'
    ],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'application': True,
}
