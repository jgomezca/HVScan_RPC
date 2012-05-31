


class SimplifiedComparableGT(dict):
    '''
    Creates GT structure which is easily an be used for coamparing GT for.
    Structure is dictionary based. Key of dict is pairs of record-label and
    value - tag pfn
    '''
    def __init__(self, gt):
        self.gt_name = gt['header']['GlobalTagName']
        self._mapping = {}
        self._generate_mapping(gt)

    def get_name(self):
        return self.gt_name

    def _generate_mapping(self, gt):
        """makes dictionary where keys: record + label and values :tag + pfn"""

        for gt_entry in gt['body']:
            key = (gt_entry['record'], gt_entry['label'])
            value = (gt_entry['tag'], gt_entry['pfn'])
            self[key] = value

    name = property(get_name)


def compare_gt(gt1, gt2, *args):
    '''
    Comparing GT. Input global tags dictionaries. Result is a dictionary
    containing having following structure:
    {
        'head': {'gt_names': [u'GT1', u'GT2', .., GTn]}
        'body':[
            (u'Rrd1', 'lb1'): {
                'pfns': [u'pfn1', u'pfn2', .. , u'pfnN'],
                'pfns_identical': True/False,
                'tags': [u'tag1', u'tag2', .. , u'tagN'],
                'tags_identical': True/False
            },
            (u'Rrd2', 'lb2'): {
                'pfns': [u'pfn1', u'pfn2', .. , u'pfnN'],
                'pfns_identical': True/False,
                'tags': [u'tag1', u'tag2', .. , u'tagN'],
                'tags_identical': True/False
            },
            ...
        ]
    }
    '''
    response = {}
    simple_gts =  [ SimplifiedComparableGT(gt1), SimplifiedComparableGT(gt2) ]
    for arg in args:
        simple_gts.append( SimplifiedComparableGT(arg) )
    keys = set()
    response['head'] = {}
    response['head']['gt_names'] = [gt.name for gt in simple_gts]
    response['body'] = {}
    for gt in simple_gts:
        keys.update(gt.keys())
    for key in keys:
        values = []
        for gt in simple_gts:
            values.append( gt.get(key, (None, None)) )
        tags = [value[0] for value in values]
        pfns = [value[1] for value in values]
        tags_identical = len(set(tags)) == 1
        pfns_identical = len(set(pfns)) == 1
        if tags_identical and pfns_identical:
            continue
        response['body'][key] = {}
        response['body'][key]['tags'] = tags
        response['body'][key]['pfns'] = pfns
        response['body'][key]['tags_identical'] = tags_identical
        response['body'][key]['pfns_identical'] = pfns_identical
    return response
