from swmmio import swmmio
mymodel = swmmio.Model("hague_model/v2014_Hague_EX_10yr_MHHW_mod2.inp")
nodes = mymodel.nodes()
cons = mymodel.conduits()
subs = mymodel.subcatchments()

def get_upstream_nodes_one(node_id, con_df, ids=[]):
    conids = con_df[con_df["OutletNode"] == node_id].index
    if len(conids)>0:
        us_node_ids = con_df["InletNode"].loc[conids].tolist()
        print us_node_ids
        return ids.extend(us_node_ids)
    else:
        return ids

def get_upstream_nodes(node_id):
    l = get_upstream_nodes_one(node_id, cons)
    for n in l:
        l.extend(get_upstream_nodes_one(n, cons, l))
        print l
    return l

def get_contributing_subs(node_id):
    us_nodes = get_upstream_nodes(node_id, cons)
    us_subs = subs[subs["Outlet"].isin(us_nodes)]
    return us_subs

def get_contributing_area(node_id):
    cont_subs = get_contributing_subs(node_id)
    return cont_subs["Area"].sum()

us_nodes = get_upstream_nodes("F143701")
print "yea"
# a0 = get_contributing_area("St1")
# a1 = get_contributing_area("E143351")
# a2 = get_contributing_area("E144050")
# a3 = get_contributing_area("E146004")


