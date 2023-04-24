from flask import Flask, redirect, request, render_template, url_for, make_response
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.express as px
from sklearn.tree import DecisionTreeRegressor
from plotly.subplots import make_subplots
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os, csv

port = int(os.environ.get("PORT", 5000))

app = Flask(__name__)

# Replace with actual values from your Spotify developer dashboard
client_id = ''
client_secret = ''

# Create the auth manager object with client ID, secret, redirect URI, and scopes
auth_manager = SpotifyOAuth(client_id, client_secret, redirect_uri='http://127.0.0.1:5000/callback',
                            scope='user-library-read,user-top-read,user-read-recently-played,user-read-playback-state,user-modify-playback-state,user-read-currently-playing,playlist-read-private,playlist-modify-public,playlist-modify-private,user-follow-read,user-read-email,user-read-private',
                            cache_handler=None)


@app.route('/')
def index():
    # Get authorization URL
    auth_url = auth_manager.get_authorize_url()

    return render_template('index.html', auth_url=auth_url)


@app.route('/callback')
def callback():
    """
    Handles the Spotify authentication callback and retrieves the access token.
    Stores the access token as a cookie and redirects to the success page.
    """
    # Retrieve the authorization code from the URL query parameters
    auth_code = request.args.get("code")

    # Use the authorization code to get an access token
    token = auth_manager.get_access_token(auth_code, as_dict=True, check_cache=False)

    # Store the access token as a cookie in the user's session
    response = make_response(redirect(url_for("success")))
    response.set_cookie("access_token", token["access_token"])
    response.set_cookie("refresh_token", token["refresh_token"])

    return response


@app.route('/success')
def success():
    # Get the access token from the user's session
    access_token = request.cookies.get('access_token')

    # Create Spotipy object with the authenticated access token
    sp = spotipy.Spotify(auth=access_token)

    # Use the Spotipy instance to retrieve the user's basic information
    user_info = sp.current_user()
    display_name = user_info['display_name']
    email = user_info['email']
    followers = user_info['followers']['total']
    country = user_info['country']
    profile_picture = user_info.get('images', [{}])[0].get('url') if user_info.get('images') else None

    # Render the HTML template and pass in the user's basic information
    return render_template('su.html', display_name=display_name, email=email, followers=followers, country=country, user_profile_picture=profile_picture)

def generate_chart(df):
    # Define the features to include in the chart
    features = ['Danceability', 'Energy', 'Loudness', 'Speechiness', 'Acousticness',
                'Instrumentalness', 'Liveness', 'Valence']

    # Group the DataFrame by playlist and calculate the mean values of each feature
    df = df.groupby(['Playlist'])[features].mean().reset_index()

    # Calculate the mean values of the audio features for the entire playlist
    danceability = df['Danceability'].mean()
    energy = df['Energy'].mean()
    loudness = df['Loudness'].mean()
    speechiness = df['Speechiness'].mean()
    acousticness = df['Acousticness'].mean()
    instrumentalness = df['Instrumentalness'].mean()
    liveness = df['Liveness'].mean()
    valence = df['Valence'].mean()

    # Generate a message based on the audio features

    if valence >= 0.8 and energy >= 0.8 and danceability >= 0.7:
        message = 'Your Spotify playlist is perfect for getting pumped up and feeling good! The high valence, energy, and danceability levels make for a super fun listening experience!'
    elif acousticness >= 0.7 and instrumentalness >= 0.7 and valence >= 0.5:
        message = 'Based on your listening habits, it looks like you prefer relaxing and chill songs that are perfect for unwinding after a long day! Your Spotify playlist has plenty of mellow tracks that are great for relaxing.'
    elif speechiness >= 0.7 and energy >= 0.6:
        message = 'Your Spotify playlist has plenty of powerful and energetic music with strong beats and heavy bass! These songs are perfect for working out or pushing yourself to the limit.'
    elif energy >= 0.8 and loudness >= 0.6 and speechiness >= 0.4:
        message = 'Your Spotify playlist is full of high-energy tracks with great beats and powerful vocals! These songs are perfect for getting pumped up and ready to take on the day.'
    elif valence <= 0.3 and acousticness >= 0.7:
        message = 'Your Spotify playlist has a lot of moody, atmospheric songs that are perfect for introspection and reflection. With high acousticness levels and low valence scores, these tracks are great for setting a mellow and contemplative mood.'
    elif valence >= 0.5 and liveness >= 0.6:
        message = 'Your Spotify playlist has lots of live music recordings that capture the energy and excitement of a live performance! With high liveness levels and moderate to high valence scores, these tracks are perfect for feeling the thrill of being at a concert.'
    elif instrumentalness <= 0.3 and danceability >= 0.7 and speechiness >= 0.4:
        message = 'Your Spotify playlist is full of upbeat, danceable tracks with catchy lyrics and hooks! With low instrumentalness levels and high danceability and speechiness scores, these songs are perfect for singing along and getting your groove on.'
    elif energy <= 0.3 and speechiness <= 0.3 and danceability <= 0.3:
        message = 'Your Spotify playlist has a lot of slow and relaxing songs that are perfect for winding down and getting some rest. These tracks have low energy, speechiness, and danceability levels, making them great for calming the mind and body.'
    elif acousticness >= 0.8 and liveness <= 0.2:
        message = 'Your Spotify playlist has a lot of soft and gentle songs that are perfect for creating a cozy and intimate atmosphere. With high acousticness and low liveness levels, these tracks are great for setting a romantic or peaceful mood.'
    elif valence < 0.5 and energy < 0.5 and danceability < 0.5:
        message = 'Your Spotify playlist contains songs with low energy, low valence, and low danceability. These tracks are often more introspective and downbeat, and can be perfect for quiet reflection or relaxation.'
    elif instrumentalness >= 0.7 and speechiness <= 0.3:
        message = 'Your Spotify playlist has a lot of instrumental music with minimal vocals that is great for focusing or studying! With high instrumentalness levels and low speechiness scores, these tracks can help you concentrate and stay productive.'
    elif danceability >= 0.8 and valence >= 0.6:
        message = 'Your Spotify playlist is full of energetic and upbeat songs with positive lyrics and catchy hooks! With high danceability and valence scores, these tracks are perfect for feeling happy and carefree.'
    else:
        message = 'You have a diverse range of music in your Spotify playlist that spans multiple genres and styles. Keep exploring new artists and songs to add even more variety!'

    print(message)

    # Create a polar chart of the audio features for each playlist and update the chart layout to include the message
    fig = go.Figure()
    for index, row in df.iterrows():
        fig.add_trace(go.Scatterpolar(
            r=row[features].tolist(),
            theta=features,
            fill='toself',
            name=row['Playlist'],
            hovertemplate="%{r:.2f}"
        ))

    fig.update_layout(
        template='seaborn',
        polar=dict(
            radialaxis=dict(showticklabels=False, ticks='', range=[0, 1])
        ),
        margin=dict(r=0),
        title="Playlist audio features Polar Diagram"
    )

    return fig, message

# Route to display the form for entering playlist information
@app.route('/pg')
def pg():
    return render_template('pg.html')


# Route to generate the chart
@app.route('/generate-csv', methods=['POST'])
def generate_chart_route():
    # Get the access token from the user's session
    access_token = request.cookies.get('access_token')

    # Create Spotipy object with the authenticated access token
    sp = spotipy.Spotify(auth=access_token)

    # Get the playlists entered by the user
    playlists = {}
    i = 0
    while True:
        name = request.form.get(f'name{i}')
        url = request.form.get(f'url{i}')
        if not name or not url:
            break  # Stop when no more entries are found
        playlists[name] = url
        i += 1

    # Create an empty DataFrame to store the track information
    df = pd.DataFrame(columns=[
        ('Playlist', str),
        ('Track Name', str),
        ('Artist', str),
        ('Album', str),
        ('URI', str),
        ('Danceability', float),
        ('Energy', float),
        ('Key', int),
        ('Loudness', float),
        ('Mode', int),
        ('Speechiness', float),
        ('Acousticness', float),
        ('Instrumentalness', float),
        ('Liveness', float),
        ('Valence', float),
        ('Tempo', float),
        ('Duration', int),
        ('Genre', str)
    ])

    # Iterate over the playlists dictionary
    for name, playlist_url in playlists.items():
        # Get the playlist ID from the URL
        playlist_id = playlist_url.split(':')[2]
        # Use the playlist ID to get the tracks in the playlist
        results = sp.playlist_tracks(playlist_id)
        # Iterate over the results to get the track information
        for item in results['items']:
            track = item['track']
            # Use the track URI to get more detailed audio features for the track
            audio_features = sp.audio_features(track['uri'])[0]
            # Use the artist name to get the genre of each artist
            artists = [artist['name'] for artist in track['artists']]
            genres = []
            for artist in artists:
                result = sp.search(q='artist:' + artist, type='artist')
                if len(result['artists']['items']) > 0:
                    genres.extend(result['artists']['items'][0]['genres'])
            # Join the list of genres into a comma-separated string
            genres_str = ', '.join(genres)
            # Add the track information to the DataFrame, including the new audio features and genre information
            df = pd.concat([df, pd.DataFrame({
                'Playlist': name,
                'Track Name': track['name'],
                'Artist': ', '.join(artists),
                'Album': track['album']['name'],
                'URI': track['uri'],
                'Danceability': float(audio_features['danceability']),
                'Energy': float(audio_features['energy']),
                'Key': int(audio_features['key']),
                'Loudness': float(audio_features['loudness']),
                'Mode': int(audio_features['mode']),
                'Speechiness': float(audio_features['speechiness']),
                'Acousticness': float(audio_features['acousticness']),
                'Instrumentalness': float(audio_features['instrumentalness']),
                'Liveness': float(audio_features['liveness']),
                'Valence': float(audio_features['valence']),
                'Tempo': float(audio_features['tempo']),
                'Duration': int(audio_features['duration_ms']),
                'Genre': genres_str,
            }, index=[0])], ignore_index=True)

    # Generate the polar chart of audio features and sentiment analysis message
    fig, message = generate_chart(df)

    # Convert the chart to HTML
    chart_html = fig.to_html(full_html=False, default_height=500, default_width=700)

    # Render the HTML template with the chart and message
    return render_template('pgv.html', chart=chart_html, message=message)

@app.route('/recently_played')
def recently_played():
    # Get the access token from the user's session
    access_token = request.cookies.get('access_token')

    # Create Spotipy object with the authenticated access token
    sp = spotipy.Spotify(auth=access_token)

    # Get user's recently played tracks
    recently_played_data = sp.current_user_recently_played()

    if len(recently_played_data['items']) > 0:
        # Parse track data and group by timestamp (hour)
        timestamps = [item['played_at'] for item in recently_played_data['items']]
        timestamps = pd.to_datetime(timestamps).tz_convert(None)  # remove timezone info
        timestamps = timestamps.floor('H')
        counts = pd.Series(np.ones(len(timestamps)), index=timestamps)
        counts = counts.groupby(level=0).sum()
        counts_list = counts.tolist()

        # Format timestamps as strings in "%I %p" format (e.g. "12 PM")
        labels = [dt.strftime("%I %p") for dt in counts.index]

        # Create plotly figure with listening history data
        fig = go.Figure(data=[go.Pie(values=counts.values, labels=labels)])
        fig.update_layout(title='Listening History Over Time')
        fig.update_traces(hole=.4, hoverinfo="label+value")

        # Convert to HTML
        chart_html = fig.to_html(full_html=False)

        # Render the HTML template and update the chart
        rendered_html = render_template('rp.html', chart_html=chart_html, recently_played_data=recently_played_data)
        final_html = rendered_html + '<script>document.getElementById("chart").innerHTML = \'' + chart_html.replace('\n', '') + '\';</script>'
        return final_html

    else:
        return 'No recently played tracks available!'

@app.route('/current_song')
def current_song():
    # Get the access token from the user's session
    access_token = request.cookies.get('access_token')

    # Create Spotipy object with the authenticated access token
    sp = spotipy.Spotify(auth=access_token)

    # Try to get the user's currently playing track
    currently_playing_data = sp.current_user_playing_track()

    if currently_playing_data is not None:
        # If the user is currently playing something, extract the song and artist names
        song_name = currently_playing_data['item']['name']
        artist_name = currently_playing_data['item']['artists'][0]['name']

        # Extract the Spotify track URI from the currently playing track data
        spotify_track_uri = currently_playing_data['item']['uri'].split(":")[-1]

        playing_status = f'{song_name} by {artist_name}'

    else:
        # If the user is not currently playing anything, get their recently played tracks
        recently_played_data = sp.current_user_recently_played()

        if len(recently_played_data['items']) > 0:
            # If there are recently played tracks, extract the most recent one's song and artist names
            last_played_data = recently_played_data['items'][0]
            song_name = last_played_data['track']['name']
            artist_name = last_played_data['track']['artists'][0]['name']

            # Extract the Spotify track URI from the most recently played track data
            spotify_track_uri = last_played_data['track']['uri'].split(":")[-1]

            playing_status = f'{song_name} by {artist_name}'

        else:
            # If there are no recently played tracks or currently playing track, set a default status
            playing_status = None

    # Render the HTML template and pass the playing status and Spotify track URI data to it
    return render_template('cr.html', playing_status=playing_status, spotify_track_uri=spotify_track_uri)

def get_user_top_tracks(sp, limit=50):
    # Create empty list to hold DataFrames for each time range
    dfs = []

    # Iterate over time ranges and retrieve top tracks for each
    for time_range in ('short_term', 'medium_term', 'long_term'):
        offset = 0
        audio_features_list = []

        while True:
            # Get user's top tracks for the current time range and offset
            top_tracks = sp.current_user_top_tracks(limit=limit, time_range=time_range, offset=offset)

            # If there are no more tracks, break out of the loop
            if not top_tracks['items']:
                break

            # Iterate over the user's top tracks and retrieve their audio features
            for i, track in enumerate(top_tracks['items']):
                # Retrieve the audio features for the track
                audio_features = sp.audio_features(track['id'])[0]

                # Add additional information to the audio features dictionary
                audio_features['Index'] = i + 1
                audio_features['Track Name'] = f'<a href="{track["external_urls"]["spotify"]}">{track["name"]}</a>'
                audio_features['Album'] = track['album']['name']
                audio_features['Artist'] = track['artists'][0]['name']
                audio_features['Release Date'] = track['album']['release_date']
                artist_info = sp.artist(track['artists'][0]['id'])
                audio_features['Genres'] = ','.join(artist_info['genres'])

                # Add the audio features dictionary to the list
                audio_features_list.append(audio_features)

            # Increment the offset to get the next page of results
            offset += limit

        # Convert list of dictionaries to Pandas DataFrame
        df = pd.DataFrame(audio_features_list)

        # Reorder the columns in the DataFrame
        df = df[['Index', 'Track Name', 'Artist', 'Album', 'Genres', 'Release Date']]

        # Append the DataFrame to the list of DataFrames
        dfs.append(df)

    return dfs

@app.route('/user_top_tracks')
def user_top_tracks():
    # Get the access token from the user's session
    access_token = request.cookies.get('access_token')

    # Create Spotipy object with the authenticated access token
    sp = spotipy.Spotify(auth=access_token, requests_timeout=40)

    # Get the user's top tracks for each time range as a list of DataFrames
    dfs = get_user_top_tracks(sp)

    # Convert the list of DataFrames to a JSON object
    json_data = {}
    for i, df in enumerate(dfs):
        time_range = ('short_term', 'medium_term', 'long_term')[i]
        json_data[time_range] = df.to_dict(orient='records')

    # Render the HTML template with the JSON data
    return render_template('tp.html', data=json_data)


# Function to retrieve user's top albums for a given time range
def get_user_top_albums(sp, time_range='medium_term', limit=50):
    # Get the user's top tracks from the Spotify API
    top_tracks = sp.current_user_top_tracks(limit=limit, time_range=time_range)

    # Create an empty list to hold the details for each album
    album_details_list = []

    # Iterate over the user's top tracks and retrieve their associated albums
    for i, track in enumerate(top_tracks['items']):
        album_id = track['album']['id']

        # Retrieve the details for the album
        album_details = {}
        album_details['Album ID'] = album_id
        album_details[
            'Album Name'] = f'<a href="{track["album"]["external_urls"]["spotify"]}">{track["album"]["name"]}</a>'
        album_details['Artist'] = track['artists'][0]['name']
        album_details['Release Date'] = track['album']['release_date']
        album_details['Total Tracks'] = track['album']['total_tracks']

        # Add the album details dictionary to the list
        album_details_list.append(album_details)

    # Convert list of dictionaries to Pandas DataFrame
    df = pd.DataFrame(album_details_list)

    # Add a new column to the DataFrame that displays the album ranking as 1-2-3
    df['Index'] = df.index + 1

    # Reorder the columns in the DataFrame
    df = df[['Index', 'Album ID', 'Album Name', 'Artist', 'Release Date', 'Total Tracks']]

    # Split the DataFrame into separate DataFrames for each time range
    short_term_df = df.copy()
    medium_term_df = df.copy()
    long_term_df = df.copy()

    # Append the DataFrames to a list
    dfs = [short_term_df, medium_term_df, long_term_df]

    # Return the list of DataFrames
    return dfs

@app.route('/user_top_albums')
def user_top_albums():
    # Get the access token from the user's session
    access_token = request.cookies.get('access_token')

    # Create Spotipy object with the authenticated access token
    sp = spotipy.Spotify(auth=access_token)

    # Define a list of time ranges to retrieve top albums for
    time_ranges = ['short_term', 'medium_term', 'long_term']

    # Create an empty list to hold the top albums data for each time range
    data = []

    # Iterate over the time ranges and retrieve the top albums for each
    for time_range in time_ranges:
        # Get the user's top albums for the current time range
        dfs = get_user_top_albums(sp, time_range=time_range, limit=20)

        # Append the DataFrame and time range to the data list as a tuple
        data.append((dfs, time_range))

    # Render the HTML template with the data
    return render_template('ta.html', data=data)


# Function to retrieve user's top artists for a given time range
def get_user_top_artists(sp, time_range='medium_term', limit=50):
    # Get the user's top artists from the Spotify API
    top_artists = sp.current_user_top_artists(limit=limit, time_range=time_range)

    # Create an empty list to hold the details for each artist
    artist_details_list = []

    # Iterate over the user's top artists and retrieve their details
    for i, artist in enumerate(top_artists['items']):
        # Retrieve the details for the artist
        artist_details = {}
        artist_details['Artist ID'] = artist['id']
        artist_details[
            'Artist Name'] = f'<a href="{artist["external_urls"]["spotify"]}">{artist["name"]}</a>'
        artist_details['Genres'] = ', '.join(artist.get('genres', ['Unknown Genres']))
        artist_details['Popularity'] = artist.get('popularity', 'Unknown Popularity')

        # Add the artist details dictionary to the list
        artist_details_list.append(artist_details)

    # Convert list of dictionaries to Pandas DataFrame
    df = pd.DataFrame(artist_details_list)

    # Add a new column to the DataFrame that displays the artist ranking as 1-2-3
    df['Index'] = df.index + 1

    # Reorder the columns in the DataFrame
    df = df[['Index', 'Artist ID', 'Artist Name', 'Genres', 'Popularity']]

    # Split the DataFrame into separate DataFrames for each time range
    short_term_df = df.copy()
    medium_term_df = df.copy()
    long_term_df = df.copy()

    # Append the DataFrames to a list
    dfs = [short_term_df, medium_term_df, long_term_df]

    # Return the list of DataFrames
    return dfs


@app.route('/user_top_artists')
def user_top_artists():
    # Get the access token from the user's session
    access_token = request.cookies.get('access_token')

    # Create Spotipy object with the authenticated access token
    sp = spotipy.Spotify(auth=access_token)

    # Define a list of time ranges to retrieve top artists for
    time_ranges = ['short_term', 'medium_term', 'long_term']

    # Create an empty list to hold the top artists data for each time range
    data = []

    # Iterate over the time ranges and retrieve the top artists for each
    for time_range in time_ranges:
        # Get the user's top artists for the current time range
        dfs = get_user_top_artists(sp, time_range=time_range, limit=20)

        # Append the DataFrame and time range to the data list as a tuple
        data.append((dfs, time_range))

    # Render the HTML template with the data
    return render_template('tr.html', data=data)

def get_user_top_tracks_by_decade(sp, limit=50):
    # Get user's top tracks for the long-term time range and offset
    top_tracks = sp.current_user_top_tracks(limit=limit, time_range='long_term')

    # Create empty list to hold track release year
    years = []

    # Iterate over the user's top tracks and retrieve their album release date
    for i, track in enumerate(top_tracks['items']):
        album = sp.album(track['album']['id'])
        years.append(int(album['release_date'][:4]))

    # Convert list of years to Pandas Series
    years_series = pd.Series(years)

    # Bin the years by decade
    decades = pd.cut(years_series, bins=range(1920, 2031, 10), labels=[f"{decade}s" for decade in range(1920, 2030, 10)])

    # Count the number of tracks in each decade
    track_counts = decades.value_counts().sort_index()

    return track_counts

@app.route('/user_top_tracks_by_decade')
def user_top_tracks_by_decade():
    # Get the access token from the user's session
    access_token = request.cookies.get('access_token')

    # Create Spotipy object with the authenticated access token
    sp = spotipy.Spotify(auth=access_token, requests_timeout=40)

    # Get the user's top tracks as a DataFrame with the count of tracks by decade
    track_counts = get_user_top_tracks_by_decade(sp)

    # Calculate the percentage of tracks in each decade
    percent_counts = track_counts / track_counts.sum() * 100

    # Create a horizontal bar chart with the decades as percentages along the x-axis and the count of tracks along the y-axis
    fig = px.bar(percent_counts, x=percent_counts.values, y=percent_counts.index, orientation='h', title='Top Tracks by Decade')

    # Render the chart as a Plotly HTML div
    graph_div = fig.to_html(full_html=False)

    # Render the HTML template with the chart div
    return render_template('tpd.html', graph=graph_div)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)
