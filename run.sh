BASE_DIR=$(cd $(dirname $0); pwd)

MOD_DIR=$BASE_DIR/modules
cd $MOD_DIR

trap 'kill 0' INT TERM EXIT

log_dir=logs/`date +%Y%m%d-%H%M%S`
mkdir -p $log_dir

echo 'Start Video Process'
python3 video_process.py | tee $log_dir/video.log &
echo 'Start ASR'
python3 asr.py | tee $log_dir/asr.log &
echo 'Start VAP'
python3 text_vap.py | tee $log_dir/text_vap.log &
echo 'Start Dialogue Backend'
python3 dialogue.py | tee $log_dir/dialogue.log &
echo 'Start TTS'
python3 tts.py | tee $log_dir/tts.log &
echo 'Start TIMEOUT'
python3 time_out.py | tee $log_dir/timeout.log &
wait
