'''
This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <http://unlicense.org/>
'''


import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio
import plotly.offline as pyo
import plotly.express as px
import base64

####################################### DATA
input_folder = "data/in/"
output_folder = "data/out/"

#network_name = "Polkadot"
network_name = "Kusama"

if network_name == "Polkadot":
    token_name = "DOT"
    decimals = 10
    values_file_name = f"{input_folder}polkadot.csv"
    labels_file_name = f"{input_folder}polkadot_labels.csv"
    filter_min_balance = 10000
else:
    token_name = "KSM"
    decimals = 12
    values_file_name = f"{input_folder}kusama.csv"
    labels_file_name = f"{input_folder}kusama_labels.csv"
    filter_min_balance = 1000

x_axis_column = "timestamp"
x_axis_label = "Time"
y_axis_label = f'{token_name} Balance'

#filter_top_min_rank = 7
#filter_top_max_rank = None

# Read the in.csv into a dataframe
values_df = pd.read_csv(values_file_name)
# only take the left 19 characters of the timestamp
values_df[x_axis_column] = values_df[x_axis_column].str.slice(0, 19)
# convert the timestamp column to a datetime object
values_df[x_axis_column] = pd.to_datetime(values_df[x_axis_column], format='%Y-%m-%d %H:%M:%S')

# normalize the balances for humans
values_df['balance'] = values_df['balance'] / (10 ** decimals)

labels_df = pd.read_csv(labels_file_name)

# Get the unique addresses
unique_addresses = values_df['address'].unique()


def sort_addresses_by_highest_balance(df):
    # Group by address and get the last timestamp for each address
    last_timestamps = df.groupby('address')[x_axis_column].max()

    # Create a MultiIndex from the last_timestamps items
    last_timestamps_index = pd.MultiIndex.from_tuples(last_timestamps.items(), names=['address', x_axis_column])

    # Filter the DataFrame using the last timestamps for each address
    last_balances = df[df.set_index(['address', x_axis_column]).index.isin(last_timestamps_index)]


    # Sort the filtered DataFrame by balance in descending order and select the addresses within the specified rank range
    selected_addresses = last_balances.sort_values(by='balance', ascending=False)

    return selected_addresses

def filter_top_addresses(df, min_rank=None, max_rank=None, min_balance=0):
    
    selected_addresses = sort_addresses_by_highest_balance(df)

    if min_rank is not None:
        if max_rank is None:
            max_rank = len(df["address"].unique()) - 1

        selected_addresses = selected_addresses.iloc[min_rank:max_rank+1]

    if min_balance > 0:
        selected_addresses = selected_addresses[selected_addresses["balance"] > min_balance]

    return selected_addresses["address"]

#top_addresses = filter_top_addresses(values_df, filter_top_min_rank, filter_top_max_rank)
top_addresses = filter_top_addresses(values_df, min_balance=filter_min_balance)

# The title of the chart
# top is determined by the filter_top_min_rank and filter_top_max_rank variables
# if filter_top_max_rank is None, then the top is determined by the number of addresses in the dataset
chart_title = f'{y_axis_label} over {x_axis_label} on {network_name}'
chart_subtitle = f'Top {len(top_addresses)} addresses with a balance of at least {filter_min_balance} {token_name}'

####################################### VISUALIZATION

# Read and encode the local logo
with open("logo.png", "rb") as f:
    logo_image = f.read()
    logo_base64 = base64.b64encode(logo_image).decode("ascii")

# Initialize an empty list to store the traces
traces = []


# A list of 20 different light colors
color_scale = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    "#aec7e8", "#ffbb78", "#98df8a", "#ff9896", "#c5b0d5",
    "#c49c94", "#f7b6d2", "#c7c7c7", "#dbdb8d", "#9edae5"
]

# Create a line trace for each unique address
for index, address in enumerate(top_addresses):
    address_df = values_df[values_df['address'] == address]
    # sort the dataframe by block number
    label = labels_df[labels_df['Address'] == address]['Chain'].values[0]
    color = color_scale[index % len(color_scale)]
    address_df = address_df.sort_values(by=x_axis_column)
    trace = go.Scatter(
        x=address_df[x_axis_column],
        y=address_df['balance'],
        mode='lines',
        name=f'{label}',
        marker=dict(
            color=color, 
        ),
        line=dict(
            width=3,
        )
    )
    traces.append(trace)


# Create a layout
layout = go.Layout(
    title={
        'text': chart_title,
        'xanchor': 'center',
        'x': 0.5,
    },
    xaxis=dict(title=x_axis_label),
    yaxis=dict(title=y_axis_label),
    images=[dict(
        source="data:image/png;base64,{}".format(logo_base64),
        xref="paper", yref="paper",
        x=0.05, y=1.02,
        sizex=0.15, sizey=0.15,
        xanchor="center", yanchor="bottom"
      )],
    font=dict(
        family="Roboto Slab, monospace",
        size=16,
        color="#8DC0F0"
    ),
)

# Create a Figure object
fig = go.Figure(data=traces, layout=layout)

# Apply the plotly_dark theme
fig.update_layout(template='plotly_dark')


# Add a subtitle
fig.add_annotation(
    xref='paper', yref='paper',
    x=0.5325, y=1.05,
    text=chart_subtitle,
    showarrow=False,
    font=dict(size=14),
    )

# Configure the plot to render in a new browser tab
pio.renderers.default = 'browser'

# Plot the figure
pyo.plot(fig, filename=f'{output_folder}{network_name}.html')