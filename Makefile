sync:
	rsync -avz --delete \
		--exclude='venv/' --exclude='.git/' --exclude='__pycache__' \
		./ $(HOST):/home/pi/air-quality-monitor
