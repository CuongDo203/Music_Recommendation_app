import streamlit as st
import plotly.express as px
import base64
import pickle
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import requests
import json
from streamlit_option_menu import option_menu
import streamlit.components.v1 as components
from model import *
from spotify import *

st.set_page_config(
    page_title="Music Recommendation App",
    page_icon="image/music-store-app.png",
    layout="centered",
    initial_sidebar_state="collapsed",
)

df = px.data.iris()

@st.cache_data
def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def get_token():
    auth_string = CLIENT_ID + ":" + CLIENT_SECRET
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization" : "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type" : "client_credentials"  
    }
    result = requests.post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

def get_auth_header(token):
    return {"Authorization": "Bearer "+ token}
   
def get_track_id(song_name, artist_name):
    result = sp.search(q="artist:"+artist_name+"track:"+song_name, type='track')
    if result and result['tracks']['items']:
        return result['tracks']['items'][0]['id']
    else:
        res = sp.search(q='track:' + song_name, type='track')
        if res and res['tracks']['items']:
            return res['tracks']['items'][0]['id']
        else:
            return None

def get_song_album_cover_url(song_name, artist_name):
    search_query = f"artist:{artist_name}track:{song_name} artist:{artist_name}"
    results = sp.search(q=search_query, type="track")
    if results and results['tracks']['items']:
        track = results['tracks']['items'][0]
        album_cover_url = track['album']['images'][0]['url']
        return album_cover_url
    else:
        return 'image/logoSpotify.png'
    
def get_track_url(track_id):
    uri = "https://open.spotify.com/track/"
    if track_id != None:
        return uri + track_id
    else:
        return None

music = pickle.load(open('df.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))

music_list = music['song'].values

def recommend(song):
    index = music[music['song'] == song].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key = lambda x : x[1])
    recommend_music_names = []
    recommend_music_posters = []
    recommend_music_url = []
    for i in distances[1:11]:
        artist = music.iloc[i[0]].artist
        recommend_music_posters.append(get_song_album_cover_url(music.iloc[i[0]].song, artist))
        track_id = get_track_id(music.iloc[i[0]].song, artist_name=artist)
        recommend_music_url.append(get_track_url(track_id))
        recommend_music_names.append(music.iloc[i[0]].song)
    return recommend_music_url

def recommend_song_page(track_id):
    uri_link = 'https://open.spotify.com/embed/track/' + track_id
    components.iframe(uri_link, height=80)
    return

def user_playlist_page(playlist_id):
    st.subheader("User Playlist")
    playlist_uri = playlist_id
    uri_link = 'https://open.spotify.com/embed/playlist/' + playlist_uri
    components.iframe(uri_link, height=200)
    return

def home_page():
    img = get_img_as_base64("image/result_page.jpg")

    page_bg_img = f"""
    <style>
    [data-testid="stAppViewContainer"] > .main {{
    background-image: url("data:image/png;base64,{img}");
    background-size: 100%;
    background-position: top left;
    background-repeat: repeat;
    background-attachment: scroll;
    }}

    [data-testid="stHeader"] {{
    background: rgba(0,0,0,0);
    }}

    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)

    st.header("Music Recommendation System")

    selected_music = st.selectbox("Type or select a song from a dropdown", music_list, key='selected_music')
    
    user_playlist_url = st.text_input(label="Playlist_Url", key='playlist_url', placeholder='Type or paste url here')
    with st.expander("Here's how to find any Playlist URL in Spotify"):
            st.write(""" 
                - Search for Playlist on the Spotify app
                - Right Click on the Playlist you like
                - Click "Share"
                - Choose "Copy link to playlist"
            """)
            st.markdown("<br>", unsafe_allow_html=True)
            st.image('image/spotify_get_playlist_url.png')
    if user_playlist_url:
        playlist_id = user_playlist_url.split('/')[-1]
        user_playlist_page(playlist_id=playlist_id)
        selected_model = st.radio(label='Chose the model', options=[':musical_note: :green[Spotify]', ':notes: :green[My model]'], horizontal=True,
                                  key='selected_model')

    btn1, btn2 = st.columns(2)

    with btn1:
        button = st.button(label='Song Recommendations', key="get_recommend")

    if(button):
        st.session_state['rs'] = True
        st.session_state['is_selected'] = True
        # Tao hieu ung loading
        with st.spinner("Getting Recommendations..."):
            recommend_music_url = recommend(selected_music)
            st.session_state['Recommended_songs'] = recommend_music_url
            
        # Hiển thị thông báo hoàn thành
        st.success("Done! Please go to page result")          

    with btn2:
        playlist_recomend_btn = st.button("Playlist Recommendations", key="get_playlist_rcm")
    
    if playlist_recomend_btn:
        if st.session_state.get('playlist_url') == "":
            st.error("Please type or paste the url above!")
        else:
            st.session_state['rs'] = True
            st.session_state['is_selected'] = False
            playlist_id = st.session_state.get('playlist_url')

            playlist_id = playlist_id.split('/')[-1].split('?')[0]
            results = sp.playlist(playlist_id)
            track_info = [{'name': track['track']['name'], 'id': track['track']['id']} for track in results['tracks']['items']]
            list_track_id = []
            for info in track_info:
                list_track_id.append(info['id'])
            with st.spinner("Getting Recommendations..."):
                if st.session_state.get('selected_model') == ':musical_note: :green[Spotify]':
                    SpotifyResult = []
                    for i in range(len(list_track_id)-5):
                        try:
                            ff = sp.recommendations(seed_tracks=list_track_id[i:i+5], limit=5)
                        except Exception as e:
                            print(e)
                            continue
                        for z in range(5):
                            # recommend_song_page(ff['tracks'][z]['id'])
                            SpotifyResult.append(ff['tracks'][z]['id'])
                    st.session_state['Recommended_playlists'] = SpotifyResult
                else:
                    id_name = {}
                    id_name[results['name']] = results['id'] 
                    playlist = create_necessary_outputs(results['name'], id_name,spotify_df)
                    complete_feature_set_playlist_vector, complete_feature_set_nonplaylist = generate_playlist_feature(complete_feature_set, playlist, 1.09)
                    top_music = generate_playlist_recos(spotify_df, complete_feature_set_playlist_vector, complete_feature_set_nonplaylist)
                    st.session_state['Recommended_playlists'] = top_music
            # Hiển thị thông báo hoàn thành
            st.success("Done! Please go to page result")
    return

def result_page():
    img = get_img_as_base64("image/home_page.jpg")

    page_bg_img = f"""
    <style>
    [data-testid="stAppViewContainer"] > .main {{
    background-image: url("data:image/png;base64,{img}");
    background-size: 100%;
    background-position: top left;
    background-repeat: repeat;
    background-attachment: scroll;
    }}

    [data-testid="stHeader"] {{
    background: rgba(0,0,0,0);
    }}

    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)
    if 'rs' not in st.session_state:
        st.error('Please click get recommendation on Home page!')
    else:
        if st.session_state.get('is_selected') == True:
            
            recommend_music_url = st.session_state['Recommended_songs']
            st.success('Top '+str(len(recommend_music_url))+' recommendations')
            for x in recommend_music_url:
                if x != None:
                    recommend_song_page(x.split('/')[-1])
                else:
                    st.error("Can't load this song")
            
            del st.session_state['rs']
        else:
            
            if st.session_state.get('selected_model') == ':musical_note: :green[Spotify]':
                
                SpotifyResult = st.session_state['Recommended_playlists']
                st.success('Top '+ str(len(SpotifyResult[:20])) +' recommendations')
                for j in SpotifyResult[:20]:
                    recommend_song_page(j)
            else:
                
                top_music = st.session_state['Recommended_playlists']
                st.success('Top '+ str(len(top_music['url'])) + ' recommendations')
                for x in top_music['url']:
                    recommend_song_page(x.split('/')[-1])

            del st.session_state['rs']
        del st.session_state['is_selected']
    return

def spr_sidebar():
    menu=option_menu(
        menu_title=None,
        options=['Home','Result'],
        icons=['house','book'],
        menu_icon='cast',
        default_index=0,
        orientation='horizontal'
    )
    if menu=='Home':
        st.session_state.app_mode = 'Home'
    elif menu=='Result':
        st.session_state.app_mode = 'Result'
    return


if __name__ == "__main__":
    spr_sidebar()
    if st.session_state.app_mode == 'Home':
        home_page()
    elif st.session_state.app_mode == 'Result':
        result_page()
