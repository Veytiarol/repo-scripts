
import sys
import os
import xbmc
import xbmcgui
import unicodedata
import urllib
import traceback
import inspect
from song import *
from lyrics import *
from utilities import *

try:
    current_dlg_id = xbmcgui.getCurrentWindowDialogId()
except:
    current_dlg_id = 0
current_win_id = xbmcgui.getCurrentWindowId()

# _ = sys.modules[ "__main__" ].__language__
__scriptname__ = sys.modules[ "__main__" ].__scriptname__
__version__ = sys.modules[ "__main__" ].__version__
__settings__ = sys.modules[ "__main__" ].__settings__
__language__ = sys.modules[ "__main__" ].__language__

SELECT_ITEM = ( 11, 256, 61453, )
EXIT_SCRIPT = ( 6, 10, 247, 275, 61467, 216, 257, 61448, )
CANCEL_DIALOG = EXIT_SCRIPT + ( 216, 257, 61448, )
GET_EXCEPTION = ( 216, 260, 61448, )
SELECT_BUTTON = ( 229, 259, 261, 61453, )
MOVEMENT_UP = ( 166, 270, 61478, )
MOVEMENT_DOWN = ( 167, 271, 61480, )

class GUI( xbmcgui.WindowXMLDialog ):
    def __init__( self, *args, **kwargs ):
        xbmcgui.WindowXMLDialog.__init__( self )
        self.fetchedLyrics = []
        self.current_song = Song.current()
        self.current_file = xbmc.Player().getPlayingFile()

    def onInit( self ):
        self.setup_all()
        
    def setup_all( self ):
        self.setup_variables()
        self.get_scraper()
        self.getMyPlayer()

    def get_scraper( self ):
        import lyricsScraper as lyricsScraper        
        self.LyricsScraper = lyricsScraper.LyricsFetcher()
        self.scraper_title = lyricsScraper.__title__
        self.scraper_exceptions = lyricsScraper.__allow_exceptions__

    def setup_variables( self ):
        self.artist = None
        self.song = None
        self.controlId = -1
        self.allow_exception = False


    def show_control( self, controlId ):
        self.getControl( 100 ).setVisible( controlId == 100 )
        self.getControl( 110 ).setVisible( controlId == 110 )
        self.getControl( 120 ).setVisible( controlId == 120 )
        page_control = ( controlId == 100 )

        xbmcgui.unlock()
        xbmc.sleep( 5 )
        try:
            self.setFocus( self.getControl( controlId + page_control ) )
        except:
            self.setFocus( self.getControl( controlId ) )

    def get_lyrics(self, song):
        try:
            lyrics, error = self.get_lyrics_from_memory( song )
            
            if (lyrics is None ):
                lyrics, error = self.get_lyrics_from_file( song )
            
            if ( lyrics is None ):
                lyrics, error = self.LyricsScraper.get_lyrics_thread( song )
                
                if ( lyrics is not None ):
                    try:
                        self.save_lyrics(lyrics)
                    except:
                        pass
            
            return lyrics, error
        except:
            print traceback.format_exc(sys.exc_info()[2])
            return None, __language__(30001)

    def get_lyrics_from_list( self, item ):
        lyrics = self.LyricsScraper.get_lyrics_from_list( self.menu_items[ item ] )
        self.show_lyrics( lyrics, True )

    def get_lyrics_from_memory (self, song):
        for l in self.fetchedLyrics:
            if ( l.song == song ):
                return l, None
        return None, "Could not find song in memory"

    def get_lyrics_from_file( self, song):
        lyrics = Lyrics()
        lyrics.song = song
        xbmc.sleep( 60 )
        if ( xbmc.getInfoLabel( "MusicPlayer.Lyrics" ) and (__settings__.getSetting( "show_embeded_lyrics" ) == 'true')):
            lyrics.lyrics = unicode( xbmc.getInfoLabel( "MusicPlayer.Lyrics" ), "utf-8" )
            self.save_lyrics_to_memory(lyrics)
            return lyrics, None
        try:
            lyrics_file = open( song.path(), "r" )
            lyrics.lyrics = unicode(lyrics_file.read(), "utf-8" )
            lyrics.source = __language__(30005)
            lyrics_file.close()
            self.save_lyrics_to_memory(lyrics)
            return lyrics, None
        except IOError:
            return None, IOError

    def save_lyrics(self, lyrics):
        self.save_lyrics_to_memory(lyrics)
        self.save_lyrics_to_file(lyrics)

    def save_lyrics_to_memory (self, lyrics):
        savedLyrics, error = self.get_lyrics_from_memory(lyrics.song)
        if ( savedLyrics is None ):
            self.fetchedLyrics.append(lyrics)
            self.fetchedLyrics =  self.fetchedLyrics[:10]

    def save_lyrics_to_file( self, lyrics ):
        if ( __settings__.getSetting( "save_lyrics" ) == 'true' ):
            try:
                if ( not os.path.isdir( os.path.dirname( lyrics.song.path() ) ) ):
                    os.makedirs( os.path.dirname( lyrics.song.path() ) )
                lyrics_file = open( lyrics.song.path(), "w" )
                lyrics_file.write( lyrics.lyrics.encode("utf-8") )
                lyrics_file.close()
                return True
            except IOError:
                #LOG( LOG_ERROR, "%s (rev: %s) %s::%s (%d) [%s]", __scriptname__, self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
                return False
    
    def focus_lyrics(self):
        if ( __settings__.getSetting( "smooth_scrolling" ) ):
            self.show_control( 110 )
        else:
            self.show_control( 100 )

    def show_error(self, error):
        try:
            self.getControl( 100 ).setText( error )
            self.show_control( 100 )
        except:
            pass
            #print "%s::%s (%d) [%s]" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ])
            #print traceback.format_exc(sys.exc_info()[2])
    
    def show_lyrics( self, lyrics):
        try:
            xbmcgui.lock()
            self.reset_controls()
            self.getControl( 100 ).setText( "" )
            self.getControl( 200 ).setLabel( "" )
            self.menu_items = []
            self.allow_exception = False
            if ( self.current_song == lyrics.song ):
                lyricsText = lyrics.lyrics
                if (lyricsText == "{{Instrumental}}"):
                    lyricsText = "Instrumental"
                self.getControl( 100 ).setText( lyricsText )
                splitLyrics = lyricsText.splitlines()
                for x in splitLyrics:
                    self.getControl( 110 ).addItem( x )
                
                self.getControl( 110 ).selectItem( 0 )
                
                self.focus_lyrics()
                
                self.getControl( 200 ).setEnabled( False )
                self.getControl( 200 ).setLabel( lyrics.source )
            
        finally:
            xbmcgui.unlock()

    def show_prefetch_message(self, song):
        self.reset_controls()
        self.getControl( 100 ).setText( __language__(30000) )
        self.show_control( 100 )
    
    def show_choices( self, choices ):
        xbmcgui.lock()
        for song in choices:
            self.getControl( 120 ).addItem( song[ 0 ] )
        self.getControl( 120 ).selectItem( 0 )
        self.menu_items = choices
        self.show_control( 120 )
    
    def reset_controls( self ):
        self.getControl( 100 ).reset()
        self.getControl( 110 ).reset()
        self.getControl( 120 ).reset()
        self.getControl( 200 ).setLabel( "" )
        

    def get_exception( self ):
        """ user modified exceptions """
        if ( self.scraper_exceptions ):
            artist = self.LyricsScraper._format_param( self.artist, False )
            alt_artist = get_keyboard( artist, "%s: %s" % ( _( 100 ), unicode( self.artist, "utf-8", "ignore" ), ) )
            if ( alt_artist != artist ):
                exception = ( artist, alt_artist, )
                self.LyricsScraper._set_exceptions( exception )
                self.myPlayerChanged( 2, True )

    def exit_script( self, restart=False ):
        self.close()
        if ( restart ): xbmc.executebuiltin( "XBMC.RunScript(%s)" % ( os.path.join( os.getcwd(), "default.py" ), ) )

    def onClick( self, controlId ):
        if ( controlId == 120 ):
            self.get_lyrics_from_list( self.getControl( 120 ).getSelectedPosition() )

    def onFocus( self, controlId ):
        self.controlId = controlId

    def getMyPlayer( self ):
        self.MyPlayer = MyPlayer( xbmc.PLAYER_CORE_PAPLAYER, function=self.myPlayerChanged )
        self.myPlayerChanged( 2 )

    def myPlayerChanged( self, event, force_update=False ):
        try:
            print "GUI-DEBUG: myPlayerChanged event:%s, force_update:%s" % (event, force_update)
            LOG( LOG_DEBUG, "%s (rev: %s) GUI::myPlayerChanged [%s]", __scriptname__, [ "stopped","ended","started" ][ event ] )
            if ( event < 2 ):
                self.exit_script()
            else:
                # The logic described below still has holes in it.
                # Mostly, xbmc.Player().getPlayingFile() does NOT
                # always change before we get here. Until I get something
                # better coded, I'm leaving this. 
                #
                # If we're here, we know that the song may have changed 
                # from what is stored in self.current_song. 
                # It is also possible that the current song has NOT changed.
                # Use xbmc.Player().getPlayingFile() to determine 
                # if we need to do anything
                self.show_prefetch_message(self.current_song)
                xbmc.sleep( 750 )
                playing_file = xbmc.Player().getPlayingFile()
                print "self.current_file: %s" % (self.current_file)
                print "self.current_song: %s" % (self.current_song)
                print "playing_file: %s" % (playing_file)
                if ( self.current_file != playing_file ):
                    self.current_file = playing_file
                    
                    # Unfortunately, calls to xbmc.getInfoLabel may return 
                    # information about the previous song for a while after
                    # the song has changed. Loop until it returns something new.
                    # We know that this won't loop forever since we know that the
                    # current file has changed (the previous "if")
                    song = Song.current()
                    print "Current: %s" % (self.current_song)
                    print "song: %s" % (song)
                    i = 0
                    while ( song is not None 
                            and self.current_song is not None 
                            and self.current_song == song
                            and i < 50 ):
                        i += 1
                        xbmc.sleep( 50 )
                        song = Song.current()
                    
                    if ( song and ( self.current_song != song or force_update ) ):
                        self.current_song = song
                        self.show_prefetch_message(song)
                        lyrics, error = self.get_lyrics( song )
                        if ( lyrics is not None ):
                            self.show_lyrics(lyrics)
                        else:
                            self.show_error(error)
                    
                    next_song = Song.next()
                    if ( next_song ):
                        self.get_lyrics( next_song )
                    else:
                        print "Missing Artist or Song name in ID3 tag for next track"
                        
                else:
                   lyrics, error = self.get_lyrics(self.current_song)
                   if ( lyrics is not None ):
                       self.show_lyrics(lyrics)
                   else:
                       self.show_error(error)                   
                   
                   next_song = Song.next()
                   if ( next_song ):
                       self.get_lyrics( next_song )
                   else:
                       print "Missing Artist or Song name in ID3 tag for next track"                   
                    
        except:
            pass
            #print "%s::%s (%d) [%s]" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ])
            #print traceback.format_exc(sys.exc_info()[2])

## Thanks Thor918 for this class ##
class MyPlayer( xbmc.Player ):
    """ Player Class: calls function when song changes or playback ends """
    def __init__( self, *args, **kwargs ):
        xbmc.Player.__init__( self )
        self.function = kwargs[ "function" ]

    def onPlayBackStopped( self ):
        xbmc.sleep( 300 )
        if ( not xbmc.Player().isPlayingAudio() ):
            self.function( 0 )
    
    def onPlayBackEnded( self ):
        xbmc.sleep( 300 )
        if ( not xbmc.Player().isPlayingAudio() ):
            self.function( 1 )      
    
    def onPlayBackStarted( self ):
        try:
            self.function( 2 )
        except:
            print "%s::%s (%d) [%s]" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ])
            print traceback.format_exc(sys.exc_info()[2])

def onAction( self, action ):
    actionId = action.getId()
    if ( action.getButtonCode() in CANCEL_DIALOG ):
        self.exit_script()
