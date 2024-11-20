# modules/utils.py

import yaml
import logging
import os
import paramiko
import traceback

def load_config_file(config_path='config.yaml'):
    """Load configuration from a YAML file."""
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        logging.info(f"Configuration loaded from {config_path}")
        return config
    except Exception as e:
        logging.error(f"Failed to load configuration file {config_path}: {e}")
        raise
    
def transfer_config(config):
    """
    Transfer a configuration file to the Raspberry Pi using SSH.
    
    :param config: Configuration dictionary loaded from the YAML file.
    """
    ssh = None  # Initialize ssh to None to handle exceptions properly
    try:
        # Extract Raspberry Pi details from the configuration
        rpi_config = config['rpi']
        rpi_user = rpi_config['user']
        rpi_host = rpi_config['ip']
        rpi_dest_path = rpi_config['rpi_conf_path']
        local_path = config['conf_path_local']  # Local configuration file to transfer

        # Debug: Print paths
        print(f"Local Path: {local_path}")
        print(f"Remote Path: {rpi_dest_path}")

        # Ensure the local file exists
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Local file {local_path} does not exist.")

        # Create an SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to the Raspberry Pi using key-based authentication
        ssh.connect(rpi_host, username=rpi_user, key_filename=config['id_rsa_path'])

        # Use SCP to transfer the file
        sftp = ssh.open_sftp()
        try:
            sftp.stat(os.path.dirname(rpi_dest_path))  # Ensure the remote directory exists
        except FileNotFoundError:
            print(f"Remote directory does not exist. Creating it.")
            sftp.mkdir(os.path.dirname(rpi_dest_path))

        # Transfer the file
        sftp.put(local_path, rpi_dest_path)
        print("Configuration file transferred successfully!")
        sftp.close()
    except Exception as e:
        print(f"Failed to transfer configuration file: {e}")
        traceback.print_exc()  # Print the full traceback of the exception
    finally:
        if ssh:
            ssh.close()