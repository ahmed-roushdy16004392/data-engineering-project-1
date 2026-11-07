import json
import re
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, State

DATA = 'Data/'
housing = pd.read_csv(DATA + 'housing_clean.csv')
crashes = pd.read_csv(DATA + 'crashes_clean.csv')
panel_d = pd.read_csv(DATA + 'panel_district_year.csv')
with open(DATA + 'council_districts.geojson') as f:
    districts_geo = json.load(f)

app = Dash(__name__)
server = app.server   # Render needs this line later

# ---------- dropdown options ----------
boroughs = ['All'] + sorted(housing['borough_clean'].unique())
years = ['All'] + sorted(housing['year'].unique().tolist())
districts = ['All'] + list(range(1, 52))
construction_types = ['All'] + sorted(housing['Reporting Construction Type'].unique())
severities = ['All', 'Severe injury', 'Fatal']
weekdays = ['All', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
measures = ['Affordable units', 'Serious crashes', 'Severe injuries']
district_borough = panel_d.drop_duplicates('council_final').set_index('council_final')['borough']


def dropdown(label, component_id, options):
    return html.Div([
        html.Label(label),
        dcc.Dropdown(id=component_id, options=options, value='All', clearable=False),
    ])


# ---------- layout ----------
app.layout = html.Div([
    html.H1('NYC Affordable Housing and Serious Road Crashes'),

    html.Div([
        html.Label('Search: a council district number (1-51) or a street name'),
        dcc.Input(id='search', type='text', n_submit=0, debounce=False,
                  placeholder='For example: 12, or Jerome, or Brooklyn 2022 fatal Friday. Press Enter or click Generate Report.',
                  style={'width': '100%', 'padding': '10px', 'fontSize': '16px', 'boxSizing': 'border-box'}),
    ], style={'marginBottom': '16px'}),

    html.Div([
        dropdown('Borough', 'borough', boroughs),
        dropdown('Year', 'year', years),
        dropdown('Council district', 'district', districts),
        dropdown('Construction type (housing only)', 'construction', construction_types),
        dropdown('Severity (crashes only)', 'severity', severities),
        dropdown('Weekday (crashes only)', 'weekday', weekdays),
        html.Div([
            html.Label('Map measure'),
            dcc.Dropdown(id='measure', options=measures, value='Severe injuries', clearable=False),
        ]),
    ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(3, 1fr)', 'gap': '12px'}),

    html.Button('Generate Report', id='generate', n_clicks=0,
                style={'margin': '16px 0', 'padding': '8px 20px'}),

    html.Div(id='search-results', style={'marginBottom': '12px'}),
    html.Div(id='summary', style={'fontSize': '18px', 'marginBottom': '12px'}),
    dcc.Graph(id='top-districts'),
    dcc.Graph(id='district-map'),
    dcc.Graph(id='scatter'),
    dcc.Graph(id='groups-chart'),
    html.Div(id='groups-note', style={'fontSize': '16px', 'marginBottom': '24px'}),

    html.H2('The story in four points'),
    html.Ol([
        html.Li([html.B('What we combined. '),
                 'Two NYC Open Data sets: affordable housing production by building (2,957 building records, '
                 '101,249 affordable units completed between 2022 and 2025) and serious injury crashes '
                 '(11,958 crashes: 11,033 with severe injuries and 925 fatal). We joined them by council '
                 'district and year.']),
        html.Li([html.B('Where the housing is. '),
                 'Affordable units are very unevenly spread. District 12 completed about 17,000 units, mostly '
                 'through preservation, far more than any other district. Districts 16 and 8 come next, mostly '
                 'new construction.']),
        html.Li([html.B('Where the injuries are. '),
                 'Severe injuries are concentrated in a few districts: district 8 (358), district 3 (324) and '
                 'district 17 (299).']),
        html.Li([html.B('Do the two go together? '),
                 'Across districts, loosely: the 13 districts with the most affordable units average 245 severe '
                 'injuries, against 170 for the 13 with the least (rank correlation 0.50). But inside each '
                 'district, years with more housing were not years with more injuries (rank correlation 0.05). '
                 'Larger, busier districts tend to have more of both, so this is an association between counts, '
                 'not evidence that housing causes crashes.']),
    ], style={'lineHeight': '1.5'}),

    html.H2('Limitations'),
    html.Ul([
        html.Li('All measures are counts, not rates. We have no population, traffic or road-length data, so '
                'bigger and busier districts naturally have more of everything.'),
        html.Li('About 82% of crashes could be placed in a council district (only 67% in 2024), so district '
                'totals are lower bounds. The summary line counts every crash that matches the filters.'),
        html.Li('Only about 22% of fatal crashes have coordinates, so fatal crashes are under-represented in '
                'the district charts.'),
        html.Li('17.4% of the housing buildings in the original file have no completion date and are left out '
                'of every year-based view. 29 buildings with no counted units, and blank unit-type counts, '
                'are treated as 0.'),
        html.Li('Only full years (2022 to 2025) are used, so the partial year 2026 is excluded.'),
        html.Li('Districts 8, 34 and 50 span two boroughs and are shown under their main borough.'),
        html.Li('The housing data has no street information, so a street search changes the crash figures only. '
                'Street abbreviations at the end of a name (AVE, ST, PKWY and similar) were spelled out, but '
                'other spelling variants of the same street may remain separate.'),
    ], style={'lineHeight': '1.5'}),

    html.P(['Data: ',
            html.A('Affordable Housing Production by Building',
                   href='https://data.cityofnewyork.us/Housing-Development/Affordable-Housing-Production-by-Building/hg8x-zxpr/about_data'),
            ', ',
            html.A('Serious Injury Response, Tracking and Analysis Program (SIRTA)',
                   href='https://data.cityofnewyork.us/Transportation/Serious-Injury-Response-Tracking-Analysis-Program-/xeqp-qz8h/about_data'),
            ' and City Council Districts (NYC Department of City Planning), all from NYC Open Data.'],
           style={'fontSize': '14px', 'marginTop': '24px'}),
], style={'maxWidth': '1100px', 'margin': '0 auto', 'padding': '16px'})


# ---------- filtering ----------
def apply_filters(borough, year, district, construction, severity, weekday):
    h, c = housing, crashes
    if borough != 'All':
        h = h[h['borough_clean'] == borough]
        c = c[c['borough_clean'] == borough]
    if year != 'All':
        h = h[h['year'] == year]
        c = c[c['year'] == year]
    if district != 'All':
        h = h[h['council_final'] == district]
        c = c[c['council_final'] == district]
    if construction != 'All':
        h = h[h['Reporting Construction Type'] == construction]
    if severity != 'All':
        c = c[c['severity'] == severity]
    if weekday != 'All':
        c = c[c['weekday'] == weekday]
    return h, c


def district_table(h, c):
    # one row per council district (1 to 51) with the three measures
    c = c.dropna(subset=['council_final']).copy()
    c['council_final'] = c['council_final'].astype(int)
    units = h.groupby('council_final')['All Counted Units'].sum().rename('Affordable units')
    crash_n = c.groupby('council_final').size().rename('Serious crashes')
    severe = c.groupby('council_final')['Total Severe Injuries'].sum().rename('Severe injuries')
    t = pd.concat([units, crash_n, severe], axis=1).reindex(range(1, 52)).fillna(0)
    t.index.name = 'District'
    return t.reset_index()


def district_year_table(h, c):
    # one row per district and year, used for the check over time
    c = c.dropna(subset=['council_final']).copy()
    c['council_final'] = c['council_final'].astype(int)
    units = h.groupby(['council_final', 'year'])['All Counted Units'].sum().rename('units')
    severe = c.groupby(['council_final', 'year'])['Total Severe Injuries'].sum().rename('severe')
    grid = pd.MultiIndex.from_product([range(1, 52), sorted(housing['year'].unique())],
                                      names=['council_final', 'year'])
    return pd.concat([units, severe], axis=1).reindex(grid).fillna(0).reset_index()


# words the search box understands, one list per control (order matters: "severe injuries" is a map
# measure and must be taken out of the text before "severe injury", which is a severity)
SEARCH_FIELDS = [
    ('measure', measures),
    ('severity', severities[1:]),
    ('construction', construction_types[1:]),
    ('borough', boroughs[1:]),
    ('year', years[1:]),
    ('weekday', weekdays[1:]),
]
SEARCH_LABELS = {'borough': 'Borough', 'year': 'Year', 'district': 'District', 'construction': 'Construction type',
                 'severity': 'Severity', 'weekday': 'Weekday', 'measure': 'Map measure'}


def parse_search(query):
    # pull the control values out of the search text; whatever is left is a street name
    q = ' ' + query.lower() + ' '
    if sum(' ' + b.lower() + ' ' in q for b in boroughs[1:]) > 1:
        # for example "Brooklyn Queens Expressway": treat the whole text as a street name
        return {}, ' '.join(q.split())
    found = {}
    for field, values in SEARCH_FIELDS:
        for v in values:
            p = ' ' + str(v).lower() + ' '
            if p in q:
                found[field] = v
                q = q.replace(p, ' ')
    m = re.search(r'\s(?:council\s+)?district\s+(\d{1,2})\s', q)
    if m and 1 <= int(m.group(1)) <= 51:
        found['district'] = int(m.group(1))
        q = q.replace(m.group(0), ' ')
    return found, ' '.join(q.split())


def street_results(c, query):
    # table of the worst matching streets for a street search
    if c.empty:
        return html.Div(f'No serious crashes found on streets matching "{query}" with the current filters.')
    top = (c.groupby('On Street')
             .agg(crashes=('Collision ID', 'size'), severe=('Total Severe Injuries', 'sum'),
                  fatalities=('Total Fatalities', 'sum'))
             .sort_values('crashes', ascending=False).head(10).reset_index())
    head = html.Tr([html.Th(x, style={'textAlign': 'left', 'padding': '4px 12px'})
                    for x in ['Street', 'Serious crashes', 'Severe injuries', 'Fatalities']])
    rows = [html.Tr([html.Td(r['On Street'], style={'padding': '4px 12px'}),
                     html.Td(f"{r['crashes']:,}", style={'padding': '4px 12px'}),
                     html.Td(f"{r['severe']:,.0f}", style={'padding': '4px 12px'}),
                     html.Td(f"{r['fatalities']:,.0f}", style={'padding': '4px 12px'})])
            for _, r in top.iterrows()]
    return html.Div([
        html.Div(f'Street search "{query}": {len(c):,} serious crashes on '
                 f'{c["On Street"].nunique():,} matching streets. Top 10:',
                 style={'fontWeight': 'bold', 'marginBottom': '6px'}),
        html.Table([head] + rows),
    ])


@app.callback(
    Output('search-results', 'children'),
    Output('summary', 'children'),
    Output('top-districts', 'figure'),
    Output('district-map', 'figure'),
    Output('scatter', 'figure'),
    Output('groups-chart', 'figure'),
    Output('groups-note', 'children'),
    Input('generate', 'n_clicks'),
    Input('search', 'n_submit'),
    State('borough', 'value'),
    State('year', 'value'),
    State('district', 'value'),
    State('construction', 'value'),
    State('severity', 'value'),
    State('weekday', 'value'),
    State('measure', 'value'),
    State('search', 'value'),
)
def update_report(n_clicks, n_submit, borough, year, district, construction, severity, weekday, measure, search):
    query = (search or '').strip()
    search_message = ''
    street = ''
    if query.isdigit() and 1 <= int(query) <= 51:
        district = int(query)          # a district number in the search box overrides the dropdown
        search_message = f'Showing council district {district}, from the search box.'
    elif query:
        found, street = parse_search(query)
        # words found in the search override the matching dropdowns for this run
        borough = found.get('borough', borough)
        year = found.get('year', year)
        district = found.get('district', district)
        construction = found.get('construction', construction)
        severity = found.get('severity', severity)
        weekday = found.get('weekday', weekday)
        measure = found.get('measure', measure)
        if found:
            applied = ', '.join(f'{SEARCH_LABELS[k]}: {v}' for k, v in found.items())
            search_message = html.Div('Applied from the search box: ' + applied + '.')

    h, c = apply_filters(borough, year, district, construction, severity, weekday)

    if street:
        c = c[c['On Street'].fillna('').str.contains(street, case=False, regex=False)]
        search_message = html.Div([search_message, street_results(c, street)])

    summary = (f"Affordable units: {h['All Counted Units'].sum():,.0f}  |  "
               f"Housing building records: {len(h):,}  |  "
               f"Serious crashes: {len(c):,}  |  "
               f"Severe injuries: {c['Total Severe Injuries'].sum():,.0f}  |  "
               f"Fatalities: {c['Total Fatalities'].sum():,.0f}")

    # district map
    table = district_table(h, c)
    map_fig = px.choropleth(table, geojson=districts_geo, locations='District',
                            featureidkey='properties.council_new', color=measure,
                            color_continuous_scale='Reds',
                            title=f'{measure} by council district (selected filters)')
    map_fig.update_geos(fitbounds='locations', visible=False)
    map_fig.update_layout(margin={'l': 0, 'r': 0, 't': 40, 'b': 0})

    # districts included in the housing-vs-crashes comparison
    table['Borough'] = table['District'].map(district_borough)
    pts = table if borough == 'All' else table[table['Borough'] == borough]
    if district != 'All':
        pts = pts[pts['District'] == district]

    # cross-domain chart 1: one dot per district, with median lines that split it into four corners
    sc = pts.copy()
    top_units = set(sc.nlargest(3, 'Affordable units')['District'])
    top_injuries = set(sc.nlargest(3, 'Severe injuries')['District'])
    sc['Label'] = sc['District'].map(lambda x: str(int(x)) if x in top_units | top_injuries else '')
    varies = sc['Affordable units'].nunique() > 1 and sc['Severe injuries'].nunique() > 1
    rho = sc['Affordable units'].rank().corr(sc['Severe injuries'].rank()) if len(sc) >= 3 and varies else float('nan')
    rho_text = 'not defined for this selection' if pd.isna(rho) else f'{rho:.2f}'
    scatter_fig = px.scatter(sc, x='Affordable units', y='Severe injuries', color='Borough',
                             text='Label', hover_name='District',
                             title=f'Each dot is a council district: affordable units vs severe injuries '
                                   f'(Spearman rank correlation {rho_text}; an association, not a cause)')
    scatter_fig.update_traces(textposition='top center', marker={'size': 10})
    if len(sc) >= 3:
        scatter_fig.add_vline(x=sc['Affordable units'].median(), line_dash='dash', line_color='grey',
                              annotation_text='median units', annotation_position='top')
        scatter_fig.add_hline(y=sc['Severe injuries'].median(), line_dash='dash', line_color='grey',
                              annotation_text='median injuries', annotation_position='right')

    # cross-domain chart 2: districts grouped by affordable units, average severe injuries per group
    if len(pts) >= 8:
        pts = pts.copy()
        labels = ['Least housing', 'Second', 'Third', 'Most housing']
        pts['Group'] = pd.qcut(pts['Affordable units'].rank(method='first'), 4, labels=labels)
        g = pts.groupby('Group', observed=True).agg(
            average=('Severe injuries', 'mean'), districts=('District', 'size')).reset_index()
        g['Group label'] = g['Group'].astype(str) + ' (' + g['districts'].astype(str) + ' districts)'
        groups_fig = px.bar(g, x='Group label', y='average', text=g['average'].round(0),
                            title='Districts grouped by affordable units completed: '
                                  'average severe injuries per district (an association, not a cause)',
                            labels={'Group label': 'Districts grouped by affordable units completed',
                                    'average': 'Average severe injuries per district'})
    else:
        groups_fig = px.bar(title='Choose a larger area (at least 8 districts) to compare district groups')

    # check over time: inside each district, do years with more housing have more injuries?
    dy = district_year_table(h, c)
    dy = dy[dy['council_final'].isin(pts['District'])].copy()
    for col in ['units', 'severe']:
        dy[col] = dy[col] - dy.groupby('council_final')[col].transform('mean')
    if len(dy) >= 12 and dy['units'].nunique() > 1 and dy['severe'].nunique() > 1:
        r = dy['units'].rank().corr(dy['severe'].rank())
        note = (f'Check over time: inside each district, the year-to-year change in affordable units and the '
                f'change in severe injuries have a rank correlation of {r:.2f} ({len(dy)} district-years). '
                f'A value near 0 means years with more housing were not years with more injuries, so a gap '
                f'between the groups above is more likely about district size and density than about housing.')
    else:
        note = 'Check over time: not enough data for this selection.'

    # top 10 districts by affordable units, split by construction type
    if h.empty:
        top_fig = px.bar(title='No housing records for this selection')
        return search_message, summary, top_fig, map_fig, scatter_fig, groups_fig, note

    d = h.groupby(['council_final', 'Reporting Construction Type'])['All Counted Units'].sum().reset_index()
    top = d.groupby('council_final')['All Counted Units'].sum().nlargest(10)
    d = d[d['council_final'].isin(top.index)].copy()
    d['District'] = 'District ' + d['council_final'].astype(int).astype(str)
    order = ['District ' + str(int(i)) for i in top.index]
    top_fig = px.bar(d, x='All Counted Units', y='District', color='Reporting Construction Type',
                     orientation='h', category_orders={'District': order},
                     title='Top 10 council districts by affordable units completed (selected filters)',
                     labels={'All Counted Units': 'Affordable units', 'Reporting Construction Type': 'Construction type'})
    return search_message, summary, top_fig, map_fig, scatter_fig, groups_fig, note


if __name__ == '__main__':
    app.run(debug=True)