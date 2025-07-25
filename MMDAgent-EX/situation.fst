#
# main fst
#

${cg_model}=asset/models/uka/MS_Uka_Humanify.pmd

${background_image}=asset/images/bg_cafe.png

${frame_image}=asset/images/desk_front.png

0 100:
    # load floor and background images
    <eps> STAGE|asset/images/floor.png,${background_image}
    # add CG model
    <eps> MODEL_ADD|0|${cg_model}
    # add basic wait motion as a loop motion
    MODEL_EVENT_ADD|0  MOTION_ADD|0|base|asset/base/wait.vmd|FULL|LOOP|ON|OFF
    # set window frame image
    <eps> WINDOWFRAME|${frame_image}
    # set camera position
    <eps> CAMERA|0,16.25,0|0,0,0|40.0|15.0

# test motion by clicking "1" - "6" key
100 100:
    KEY|1  MOTION_ADD|0|act|asset/actions/eshaku.vmd|PART|ONCE|ON|OFF
    +KEY|2 MOTION_ADD|0|act|asset/actions/ojigi.vmd|PART|ONCE|ON|OFF
    +KEY|3 MOTION_ADD|0|act|asset/actions/thinking.vmd|PART|ONCE|ON|OFF
    +KEY|4 MOTION_ADD|0|act|asset/actions/wavehand.vmd|PART|ONCE|ON|OFF
    +KEY|5 MOTION_ADD|0|act|asset/actions/wavehands.vmd|PART|ONCE|ON|OFF
    +KEY|6 MOTION_ADD|0|act|asset/actions/looking_right.vmd|PART|ONCE|ON|OFF
