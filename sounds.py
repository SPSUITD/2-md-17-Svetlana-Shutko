import arcade


SOUNDS = {
    'background_sound': "assets/sounds/sound_bg.mp3",  # !
    'artifact_activate': 'assets/sounds/art_all.mp3',  # !
    'win': 'assets/sounds/end.mp3', # !

    'mob1_attack': 'assets/sounds/mob1_a.mp3',  # !
    'mob2_attack': 'assets/sounds/mob2_a.mp3',  # !
    'mob1_exposure': 'assets/sounds/mob1_roar.mp3',  # !
    'mob1_run': 'assets/sounds/mob1_run.mp3',  # !
    'mob1_die': 'assets/sounds/mob_die.mp3',  # !

    'player_attack': 'assets/sounds/sound_attack.mp3',   # !
    'player_walk': 'assets/sounds/sound_walk.mp3',  # !
    'player_jump': 'assets/sounds/sound_jump.mp3',  # !
}

ACTIVE_SOUNDS = {

}

for name, path in SOUNDS.items():
    SOUNDS[name] = arcade.load_sound(path)


def stop_all_sounds():
    for sound, player in ACTIVE_SOUNDS.items():
        sound.stop(player)


def start_sound(name, **kw):
    if ACTIVE_SOUNDS.get(SOUNDS[name]):
        stop_sound(name)
    ACTIVE_SOUNDS[SOUNDS[name]] = SOUNDS[name].play(**kw)
    return ACTIVE_SOUNDS[SOUNDS[name]]


def stop_sound(name):
    SOUNDS[name].stop(ACTIVE_SOUNDS[SOUNDS[name]])


