#Ado Haruna
#Dept of Mechatronics Engineering
#Bayero University, Kano-Nigeria
#aharuna.mct@buk.edu.ng
#26/01/2024

import paho.mqtt.client as mqtt
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import dash_daq as daq
import time
import random
import plotly.graph_objs as go
from collections import deque
import numpy as np

#Setup MQTT client
ourClient = mqtt.Client("RPI")
MQTT_USER = 'Your MQTT username'
MQTT_PASSWORD = 'Your MQTT password'
MQTT_ADDRESS = 'MQTT host IP address"
ourClient.username_pw_set(MQTT_USER, MQTT_PASSWORD)
ourClient.connect(MQTT_ADDRESS, 1883)

#Variables
X = deque(maxlen = 20)
X.append(1)
Y = deque(maxlen = 20)
Y.append(1)
Y_ref = deque(maxlen = 20)
Y_ref.append(50)
current_R = 0
current_Y = 0
current_B = 0
Freq = 0
line_volts = 0
time_on = 0
t_sim = 60			#simulation time
#storage variables
freq_data = [0]
volt_data = [0]
crnt_data = [0]

#theme colors
theme = {
    'dark': True,
    'detail': '#007439',
    'primary': '#00EA64',
    'secondary': '#6E6E6E',
    'dark_bg2': '#323232',
    'dark_bg': '#303030'   
}

cur_gauge_colors = {
    '0': 'green',
    '2': 'red',
    '4': 'yellow',
    '6': 'green' 
}

# On message event
def message_event(client, userdata, msg):
    global current_R
    global current_Y
    global current_B
    global Freq
    global line_volts
    global time_on
    msg_str = msg.payload.decode()
    if (msg.topic == "time_on"):
        print(msg.topic + ' ' + msg_str)
        time_on = float(msg_str)
    elif (msg.topic == "R_amps"):
        print(msg.topic + ' ' + msg_str)
        current_R = float(msg_str)
    elif (msg.topic == "Y_amps"):
        print(msg.topic + ' ' + msg_str)
        current_Y = float(msg_str)
        
    elif (msg.topic == "B_amps"):
        print(msg.topic + ' ' + msg_str)
        current_B = float(msg_str)
        crnt_data.append(current_R+current_Y+current_B)
    elif (msg.topic == "Volts"):
        print(msg.topic + ' ' + msg_str)
        line_volts = float(msg_str)
        volt_data.append(line_volts)
    elif (msg.topic == "Freq"):
        print(msg.topic + ' ' + msg_str)
        Freq = float(msg_str)
        freq_data.append(Freq)

ourClient.on_message = message_event
ourClient.subscribe("Freq")
ourClient.subscribe("time_on")
ourClient.subscribe("R_amps")
ourClient.subscribe("Y_amps")
ourClient.subscribe("B_amps")
ourClient.subscribe("Volts")
ourClient.loop_start()


def FreqGauge():
    return html.Div([
        daq.Gauge(
            id = 'Freq',
            min=0,
            max=70,
            showCurrentValue=True,
            label="Frequency",
            units = "Hz",
            value=50,
            color=theme['primary'],
            className='dark-theme-control'
        ),
    ])

def VoltGauge():
    return html.Div([
        daq.Gauge(
        id = 'Voltage',
        min=0,
        max=150,
        showCurrentValue=True,
        label="Line Voltage",
        units = "V",
        value=120,
        color=theme['primary'],
        className='dark-theme-control'
    ),
])

def CurrentGauge():
    return html.Div([
        daq.Gauge(
        id = 'Current',
        min=0,
        max=10,
        showCurrentValue=True,
        label="DL Current",
        units = "Amps",
        value=5,
        color='red'
    ),
])

# Text field
def drawText():
    return html.Div([
        dbc.Card(
            dbc.CardBody([
                html.Div([
                    html.H2("Text"),
                ], style={'textAlign': 'center'}) 
            ])
        ),
    ])

def LED_display():
    return html.Div([
    daq.LEDDisplay(
        id = 'LED_display',
        value=str(t_sim), 
        backgroundColor=theme['dark_bg2'],
        color=theme['primary'],
        label='Time (s)'
    ), 
])

def power_button():
    return html.Div([
    daq.PowerButton(
        id = 'pwr_button',
        on=False,
        color=theme['primary'],
        className='dark-theme-control'
    ),
    html.Div(id='pwr_button_rslt')
])

def stop_button():
    return html.Div([
    daq.StopButton(
        id='stop_button',
        buttonText ='Save',
        n_clicks = 0,
    ),
])

def current_slider():
    return html.Div([
        dcc.Slider(0, 6,
        step=None,
        marks={
        0: 'A',
        2: 'R',
        4: 'Y',
        6: 'B',
        },
        id = 'CT_source',
        included=False,
        vertical=False,
        value=0,
        
)], 
)

def ref_knob():
    return html.Div([
        daq.Knob(
        id = 'freq_ref_knob',
         min=0,
         max=60,
         value=50,
         size = 120,
        scale={'start':50, 'labelInterval': 5, 'interval': 5},
        label = 'Reference Frequency',
         color = theme['primary']
    ), 
])
fig = go.Figure(
    data=[
    go.Scatter(x=list(X), y=list(Y))])
def freq_graph():
    return html.Div([
            dcc.Graph(
            figure=fig,
            id='frq_graph',
            style={'height': 350},
    ),   
])

# Build App
app = Dash(external_stylesheets=[dbc.themes.SLATE])

app.layout = html.Div([ 
    dbc.Card(
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Br(),
                    html.Br(),
                    FreqGauge() 
                ], width=3,align='start'),
                dbc.Col([
                    html.Br(),
                    html.Br(),
                    VoltGauge()
                ], width=3,align='start'),
                dbc.Col([
                    dbc.Row([
                    current_slider()  
                    ],align='start'),
                    dbc.Row([
                    CurrentGauge()  
                    ]),
                ], align='start',width=3),
                
                dbc.Col([
                    dbc.Row([
                        dbc.Col(
                            power_button(),
                            ),
                        dbc.Col(
                            stop_button(),
                            )],justify="evenly"),
                    dbc.Row([
                        dbc.Col(
                            html.Br(style={"line-height": "4"})),                   
                    ],align = "end"),                   
                ], width=3),
            ]),
            
            dbc.Row([
                dbc.Col([
                    freq_graph()
                    ], width=9),
                dbc.Col([
                    dbc.Row([
                      ref_knob()  
                    ],justify="center", align="center"),
                    dbc.Row([
                        LED_display(),
                    ],justify="center", align="center"),                  
                ],	width=2, align = "center",)
            ],justify="evenly",),
        ]),
        style={'backgroundColor':theme['dark_bg']}
   ),
    
    dcc.Interval(
        id='update_interval',
        n_intervals=0,
        interval=1*1000,
        disabled=False
    )
])


@app.callback(
    Output('pwr_button_rslt', 'children'),
    Input('pwr_button', 'on')
)
def update_output(on):
    return ''

@app.callback(
    Output('pwr_button', 'on'),
    Input('stop_button', 'n_clicks')
)
def update_output(n_clicks):
    print("Stopped!")
    np.savetxt('freq_dat',freq_data,fmt='%.2f')
    np.savetxt('volt_dat',volt_data,fmt='%.2f')
    np.savetxt('crnt_dat',crnt_data,fmt='%.2f')
    return False

@app.callback(
    [Output('Freq', 'value'),
     Output('Voltage', 'value'),
     Output('Current', 'value'),
     Output('Current', 'color'),
     Output('LED_display', 'value')],
    [Input('update_interval', 'n_intervals'),
     Input('CT_source', 'value')])
def update_output1(n, CT_source):
    t_on = int(time_on)
    freq = Freq
    volts = line_volts
    amps_R = current_R #random.randint(1,5)
    amps_Y = current_Y
    amps_B = current_B
    if (CT_source == 2):
        color_str ='red'
        amps = amps_R
    elif (CT_source == 4):
        color_str ='yellow'
        amps = amps_Y
    elif (CT_source == 6):
        color_str ='blue'
        amps = amps_B
    else:
        color_str = theme['primary']#,'green'
        amps = amps_R + amps_Y + amps_B
    return freq,volts,amps,color_str,str(t_on)


@app.callback(
    Output('frq_graph', 'figure'),
    [Input('update_interval', 'n_intervals'),
     Input('freq_ref_knob', 'value'),
     Input('Freq', 'value')]
)
def update_graph_scatter(n, value, Freq):
    X.append(X[-1]+1)
    #Y.append(random.randint(45,55))
    Y.append(Freq)
    if (value < 40):
        value = 40
    elif (value > 60):
        value = 60
    value=int(value)
    Y_ref.append(value)
    fig = go.Figure(
        data=[go.Scatter(x=list(X), y=list(Y),
                         name='Freq')])
    fig.add_trace(go.Scatter(x=list(X), y=list(Y_ref),
                             name='Ref'))
    fig.update_layout(title='Freqency (Hz)',
                yaxis_zeroline=False, xaxis_zeroline=False,
                paper_bgcolor= theme['dark_bg2'],
                font_color = 'yellow',
                yaxis_range = [30,70],  
                margin=go.layout.Margin(l=40, r=0, t=40, b=30))
    
    return fig

# Run app 
if __name__ == '__main__':
    app.run_server(debug=False)




