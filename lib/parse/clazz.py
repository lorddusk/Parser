def getFeature(opt_entry, featdata, subfeatdata, optfeats):
    if opt_entry['type'] == "refClassFeature":
        opt_entry = getClassFeature(opt_entry, featdata)
    elif opt_entry['type'] == "refSubclassFeature":
        opt_entry = getSubClassFeature(opt_entry, subfeatdata)
    elif opt_entry['type'] == "refOptionalfeature":
        opt_entry = getOptionalFeature(opt_entry, optfeats)
    return opt_entry


def getClassFeature(source, data):
    for feature in data:
        if source.get('classFeature', None) is not None:
            if '|' in source['classFeature']:
                optfs = source['classFeature'].split('|')
                source = {
                    "name": optfs[0],
                    "className": optfs[1],
                    "classSource": optfs[2],
                    "level": optfs[3]
                }
        if feature['name'] == source['name']:
            if feature['classSource'] == source['classSource']:
                if feature['className'] == source['className']:
                    if feature['level'] == int(source['level']) or ['level'] == source['level']:
                        return feature


def getSubClassFeature(source, data):
    for feature in data:
        if feature['name'] == source['name']:
            if feature['className'] == source['className']:
                if feature['classSource'] == source['classSource']:
                    if feature['subclassShortName'] == source['subclassShortName']:
                        if feature['subclassSource'] == source['subclassSource']:
                            if feature['level'] == int(source['level']) or feature['level'] == source['level']:
                                return feature


def getOptionalFeature(source, data):
    for feature in data:
        if source[0] == feature['name']:
            if len(source) > 1:
                if source[1] == feature['source']:
                    return feature
            else:
                return feature


def CreateClassFeature(className, featureName, text, level, source, srd):
    return {
        'name': f"{className}: {featureName}",
        'className': className,
        'text': text,
        'level': level,
        'source': source,
        'srd': srd
    }


def CreateSubclassFeature(className, subclassName, featureName, text, level, source, srd):
    return {
        'name': f"{className}: {subclassName}: {featureName}",
        'className': className,
        'subclassName': subclassName,
        'text': text,
        'level': level,
        'source': source,
        'srd': srd
    }


def CreateOptionalFeature(className, featureName, option, text, level, source, srd):
    return {
        'name': f"{className}: {featureName}: {option}",
        'className': className,
        'featureName': featureName,
        'text': text,
        'level': level,
        'source': source,
        'srd': srd
    }


def CreateClassSplit(feat):
    feature = {
        'name': feat[0],
        'className': feat[1],
        'classSource': feat[2],
        'level': feat[3],
        'source': None,
        'displayText': None,
    }

    try:
        feature['source'] = feat[4]
    except IndexError:
        pass

    if feature['source'] == '':
        feature['source'] = feature['classSource']
    if feature['classSource'] == '':
        feature['classSource'] = 'PHB'

    return feature


def CreateSubclassSplit(feat):
    feature = {
        'name': feat[0],
        'className': feat[1],
        'classSource': feat[2],
        'subclassShortName': feat[3],
        'subclassSource': feat[4],
        'level': feat[5],
        'source': None,
        'displayText': None,
    }

    try:
        feature['source'] = feat[6]
    except IndexError:
        pass

    if feature['source'] == '':
        feature['source'] = feature['subclassSource']
    if feature['classSource'] == '':
        feature['classSource'] = 'PHB'
    if feature['subclassSource'] == '':
        feature['subclassSource'] = 'PHB'

    return feature
