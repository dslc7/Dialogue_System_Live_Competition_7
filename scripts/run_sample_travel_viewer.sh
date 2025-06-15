BASE_DIR=$(cd $(dirname $0); pwd)/..

MOD_DIR=$BASE_DIR/modules
cd $MOD_DIR

trap 'kill 0' INT

echo 'Start Travel Viewer'
python3 travel_viewer.py &
echo 'Start Sample Travel Viewer'
python3 sample_travel_viewer.py &
wait
