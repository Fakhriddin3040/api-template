FROM postgres:18.6

CMD ["postgres", "-c", "logging_collector=on", \
     "-c", "log_directory=/logs", \
     "-c", "log_filename=postgresql.log", \
     "-c", "log_rotation_age=1d", \
     "-c", "log_rotation_size=10MB", \
     "-c", "config_file=/etc/postgresql/postgresql.conf"]
