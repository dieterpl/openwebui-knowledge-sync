# OpenWebUI Knowledge Sync

## Overview
OpenWebUI Knowledge Sync is a Python-based tool that enables synchronization of knowledge repositories from Git to OpenWebUI. 

## Features
- Docker containerization for simplified and consistent deployment
- Lightweight and Python implementation

## Prerequisites
- Python 3.8 or higher (recommended)
- Docker (optional, provides containerized deployment for easy setup)

## Installation

### Local Setup

1. Prepare environment configuration
   - Copy `.env.example` to `.env`
   - Configure your specific settings in the `.env` file

2. Clone the repository:
   ```
   git clone https://github.com/dieterpl/openwebui-knowledge-sync
   cd <repository-directory>
   ```

3. Build the project:
   ```
   make build
   ```

4. Run the synchronization:
   ```
   make run
   ```

## Configuration
1. Duplicate the `.env.example` file and rename it to `.env`
2. Edit the `.env` file, customizing the configuration settings to match your specific synchronization requirements

## License
Distributed under the MIT License. Refer to the `LICENSE` file for comprehensive licensing details.

## Support
Encountering issues or have questions? Please open a GitHub issue in the repository for prompt assistance.