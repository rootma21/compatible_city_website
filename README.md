# Group 15: Compatible City Dashboard
## DS 4200 Final Service-Learning Project

An interactive web visualization built for the Mass Ave Coalition to explore sidewalk accessibility along Massachusetts Avenue in Boston, MA.
Created December, 2022.

Baackground: The Mass Ave coalition is a Boston-based nonprofit organization seeking to advance the public health, transportation, and streetscape surrounding Mass Ave. 
They collaborate with a variety of stakeholders in the community to create actionable improvements regarding areas of need in the Mass Ave neighborhood.
We built this tool to help the coalition visualize the existing sidewalk data, as well as demonstrate a need for updated sidewalk width data. 

The functionalities of this dashboard built using Plotly's dash library include an interactive sidewalk accessibility map and an interactive map containing sidewalk-related 311 service requests.

The website hosted on render can be accessed at https://compatible-city-dashboard.onrender.com/
A live demo of the website can be viewed at https://drive.google.com/file/d/1LmbL3WIsmeB5K7BxNCrpmCbowvm95l12/view?usp=share_link
Data sources: 
- 311 Service Requests https://data.boston.gov/dataset/311-service-requests
- Sidewalk Inventory https://data.boston.gov/dataset/sidewalk-inventory

## How to run host the application locally from terminal:

1. Clone this repository.  
2. Install dependencies using a new environment (see instructions below)
3. Run the app using `python app.py`
4. In browser visit http://127.0.0.1:8050/

## For setting up a Conda Web-Dev environment:

1. `conda create -n webdev python=3.9`
1. `conda activate webdev`
1. `pip install -r requirements.txt`
