
def get_latest_subtopic_measures(st, states=[]):
    do_state_filter = len(states) > 0
    seen = set([])
    measures = []
    for m in st.children:
        if m.guid not in seen:
            versions = m.get_versions(include_self=True)
            versions.sort(reverse=True)
            if do_state_filter:
                versions = [v for v in versions if v.status in states]
            if versions:
                measures.append(versions[0])
            seen.add(m.guid)
    return measures
