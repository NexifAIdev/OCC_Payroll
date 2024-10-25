{
    'name': 'Matrix widget',

    'author': 'Kitworks Systems',
    'website': 'https://kitworks.systems/',

    'category': 'Extra Tools',
    'license': 'OPL-1',
    'version': '17.0.1.0.3',

    'depends': [
        'web',
    ],
    'qweb': [
        'static/src/xml/qweb_matrix_template.xml',
    ],
    'data': [
        'template/add_matrix_assets.xml',
    ],

    'installable': True,

    'images': [
        'static/description/cover.png',
        'static/description/icon.png',
    ],
    'assets': {
        'web.assets_backend': [
            'kw_matrix_widget/static/src/js/matrix.js', ],
    },

}
