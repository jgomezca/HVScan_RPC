services = {
    'prod': {
        'oracle': set(['cms_orcon_prod']),
        'frontier': set(['FrontierOnProd']),
    },
    'adg': {
        'oracle': set(['cms_orcon_adg']),
        'frontier': set(['FrontierProd', 'PromptProd']),
    },
    'int': {
        'oracle': set(['cms_orcoff_int']),
        'frontier': set(['FrontierInt']),
    },
    'prep': {
        'oracle': set(['cms_orcoff_prep']),
        'frontier': set(['FrontierPrep']),
    },
    'arc': {
        'oracle': set(['CMSARC_LB']),
        'frontier': set(['FrontierArc']),
    },
}

