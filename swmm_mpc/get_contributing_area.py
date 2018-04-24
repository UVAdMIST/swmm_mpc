from swmmio import swmmio
mymodel = swmmio.Model("../hague_model/v2014_Hague_EX_10yr_MHHW_mod2.inp")
nodes = mymodel.nodes()
cons = mymodel.conduits()
subs = mymodel.subcatchments()

def get_upstream_conduits(node_id, con_df):
    us_nodes = get_upstream_nodes(node_id, con_df)
    us_cons = con_df[(con_df.InletNode.isin(us_nodes)) | (con_df.OutletNode.isin(us_nodes))] 
    return us_cons.index

def get_upstream_nodes_one(node_id, con_df):
    conids = con_df[con_df["OutletNode"] == node_id].index
    if len(conids)>0:
        us_node_ids = con_df["InletNode"].loc[conids].tolist()
        return us_node_ids
    else:
        return []

def get_upstream_nodes(node_id, con_df):
    l = get_upstream_nodes_one(node_id, con_df)
    for n in l:
        l.extend(get_upstream_nodes_one(n, con_df))
    return l

def get_contributing_subs(node_id, con_df, subs_df):
    us_nodes = get_upstream_nodes(node_id, con_df)
    us_subs = subs_df[subs["Outlet"].isin(us_nodes)]
    return us_subs

def get_contributing_area(node_id, con_df, subs_df):
    cont_subs = get_contributing_subs(node_id, con_df, subs_df)
    return cont_subs["Area"].sum()


a0 = get_contributing_area("St1", cons, subs)
a1 = get_contributing_area("E143351", cons, subs)
a2 = get_contributing_area("E144050", cons, subs)
a3 = get_contributing_area("E146004", cons, subs)


