from dash import Dash, html, dcc, Input, Output, callback
import plotly.express as px
import json
import glob 


class Node:
    def __init__(self, id, generation, parent=None, value=-1) -> None:
        self._id = id
        self._generation = generation
        self._parent = parent
        self._value = value

    def __eq__(self, __value: object) -> bool:
        return self._id == __value._id

    def __repr__(self) -> str:
        return self._id


def item_generator(json_input, lookup_key, depth=None):
    if depth is None:
        depth = 0
    if isinstance(json_input, dict):
        for k, v in json_input.items():
            if k == lookup_key:
                yield from item_generator(v, lookup_key, depth + 1)
        yield (depth, json_input)
    elif isinstance(json_input, list):
        for item in json_input:
            yield from item_generator(item, lookup_key, depth)

target_classes = []
for file in glob.glob("assets/plots/*.svg"):
    fname = file.split("assets/plots/")[1]
    cname = fname.split("_plot.svg")[0]
    target_classes.append(f"schema:{cname}")
target_classes.sort()

top_20_target_classes = [
    "schema:ListItem",
    "schema:ImageObject",
    "schema:BreadcrumbList",
    "schema:Organization",
    "schema:WebPage",
    "schema:SearchAction",
    "schema:Offer",
    "schema:Person",
    "schema:ReadAction",
    "schema:Product",
    "schema:EntryPoint",
    "schema:PostalAddress",
    "schema:Article",
    "schema:WebSite",
    "schema:CollectionPage",
    "schema:NewsArticle",
    "schema:SiteNavigationElement",
    "schema:ContactPoint",
    "schema:Rating",
    "schema:Place",
]

data_plotly_sunburst = {"ids": [], "names": [], "parents": [], "values": []}
with open("data/count.json", "r") as file:
    parsed_json = json.load(file)

    itemlist = sorted(item_generator(parsed_json, "children"), key=lambda x: x[0])

    nodelist = []
    for generation, parent in itemlist:
        if parent.get("value") is None:
            parent["value"] = 0

        parent_node = Node(parent["@id"], generation, value=parent["value"])
        if parent_node not in nodelist:
            # print(f"Adding {parent_node} to {nodelist}")
            nodelist.append(parent_node)

        if "children" in parent.keys():
            for child in parent.get("children"):
                if child.get("value") is None:
                    child["value"] = 0
                child_node = Node(
                    child["@id"], generation, parent=parent["@id"], value=child["value"]
                )
                nodelist.append(child_node)

    for node in nodelist:
        id = node._id
        if id in data_plotly_sunburst["ids"]:
            id = f"{node._id} {node._parent} {node._generation}"
        data_plotly_sunburst["ids"].append(id)
        data_plotly_sunburst["names"].append(node._id)
        data_plotly_sunburst["values"].append(node._value)
        data_plotly_sunburst["parents"].append(node._parent)


# Initialize the app
app = Dash(__name__)
server = app.server

# App layout
app.layout = html.Div(
    [
        html.Section(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.H1(
                                    "Schema.org annotations observatory",
                                    className="title",
                                ),
                                html.H2(
                                    "Deep dive into WebDataCommons JSON-LD markup",
                                    className="subtitle",
                                ),
                            ],
                            className="container",
                        )
                    ],
                    className="hero-body",
                )
            ],
            className="hero is-dark",
        ),
        html.Section(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    children="Schema.org class hierarchy.",
                                    className="title is-5",
                                    style={"padding": 10},
                                ),
                                html.Div(
                                    children="In the following sunburst plot, the count of typed entities is displayed through the 'value' attribute.",
                                    className="content",
                                    style={"padding": 10},
                                ),
                                dcc.Graph(
                                    figure=px.sunburst(
                                        data_plotly_sunburst,
                                        ids="ids",
                                        names="names",
                                        parents="parents",
                                        values="values",
                                    ),
                                    style={
                                        "padding": 10,
                                        "width": "100%",
                                        # "height": "70vh",
                                        # "width": "70vw",
                                        "display": "inline-block",
                                        "vertical-align": "right",
                                    },
                                ),
                            ],
                            className="column is-half",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            children="Per-class top-10 property combinations.",
                                            className="title is-5",
                                        ),
                                        html.Div(
                                            children="In the following upset plots, you can select a Schema.org class and display the most used property combinations (top-10).",
                                            className="content",
                                        ),
                                        html.Div([
                                            "All these 776 plots have been rendered based on the Schema.org characteristic sets we pre-computed and made available at ", 
                                            dcc.Link(f"https://zenodo.org/record/8167689", href="https://zenodo.org/record/8167689", target="_blank"),
                                            "."
                                        ],
                                            #children="All these 776 plots have been rendered based on the Schema.org characteristic sets we pre-computed (https://zenodo.org/record/8167689)",
                                            className="content",
                                            
                                        ),
                                        dcc.Dropdown(
                                            target_classes,
                                            "schema:Product",
                                            id="class-dropdown",
                                        )
                                    ],
                                    style={"padding": 10},
                                ),
                                html.Div(
                                    id="upsetplot-container", style={"padding": 10}
                                ),
                            ],
                            className="column is-half",
                        ),
                    ],
                    className="columns",
                ),
            ]
        ),
    ]
)


@callback(Output("upsetplot-container", "children"), Input("class-dropdown", "value"))
def update_output(value):
    print(f"You have selected {value}")
    class_name = value.split("schema:")[1]
    image_path = f"assets/plots/{class_name}_plot.svg"
    return html.Img(src=image_path)


# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
