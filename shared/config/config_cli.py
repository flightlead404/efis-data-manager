#!/usr/bin/env python3
"""
Configuration management CLI for EFIS Data Manager.
Provides commands for validating, migrating, and managing configurations.
"""

import argparse
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, Any

from .config_manager import ConfigManager, SecureCredentialManager
from .validation import ConfigSchema


def validate_config_command(args):
    """Validate configuration file."""
    try:
        config_manager = ConfigManager(args.config, args.environment)
        config = config_manager.load_config()
        
        if config_manager.validate_config():
            print("✅ Configuration is valid")
            return 0
        else:
            print("❌ Configuration validation failed")
            return 1
            
    except Exception as e:
        print(f"❌ Error validating configuration: {e}")
        return 1


def create_config_command(args):
    """Create a new configuration file."""
    try:
        config_path = Path(args.output)
        
        if config_path.exists() and not args.force:
            print(f"❌ Configuration file already exists: {config_path}")
            print("Use --force to overwrite")
            return 1
        
        config_manager = ConfigManager(environment=args.environment)
        config_manager._create_default_config(config_path)
        
        print(f"✅ Created configuration file: {config_path}")
        return 0
        
    except Exception as e:
        print(f"❌ Error creating configuration: {e}")
        return 1


def migrate_config_command(args):
    """Migrate configuration to new version."""
    try:
        config_manager = ConfigManager(args.config)
        config = config_manager.load_config()
        
        # Save migrated configuration
        if args.output:
            config_manager.save_config(args.output)
            print(f"✅ Migrated configuration saved to: {args.output}")
        else:
            config_manager.save_config()
            print("✅ Configuration migrated in place")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error migrating configuration: {e}")
        return 1


def show_config_command(args):
    """Display current configuration."""
    try:
        config_manager = ConfigManager(args.config, args.environment)
        config = config_manager.load_config()
        
        if args.format == "json":
            from dataclasses import asdict
            config_dict = asdict(config)
            print(json.dumps(config_dict, indent=2))
        else:
            # YAML format
            from dataclasses import asdict
            config_dict = asdict(config)
            print(yaml.dump(config_dict, default_flow_style=False, indent=2))
        
        return 0
        
    except Exception as e:
        print(f"❌ Error displaying configuration: {e}")
        return 1


def set_config_command(args):
    """Set configuration value."""
    try:
        config_manager = ConfigManager(args.config, args.environment)
        config_manager.load_config()
        
        # Parse value as JSON if possible, otherwise treat as string
        try:
            value = json.loads(args.value)
        except json.JSONDecodeError:
            value = args.value
        
        config_manager.set(args.key, value)
        config_manager.save_config()
        
        print(f"✅ Set {args.key} = {value}")
        return 0
        
    except Exception as e:
        print(f"❌ Error setting configuration: {e}")
        return 1


def get_config_command(args):
    """Get configuration value."""
    try:
        config_manager = ConfigManager(args.config, args.environment)
        config_manager.load_config()
        
        value = config_manager.get(args.key)
        if value is not None:
            if args.format == "json":
                print(json.dumps(value))
            else:
                print(value)
        else:
            print(f"❌ Configuration key not found: {args.key}")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"❌ Error getting configuration: {e}")
        return 1


def credential_command(args):
    """Manage secure credentials."""
    try:
        credential_manager = SecureCredentialManager()
        
        if args.credential_action == "set":
            if not args.key or not args.value:
                print("❌ Both --key and --value are required for setting credentials")
                return 1
            
            if credential_manager.store_credential(args.key, args.value):
                print(f"✅ Credential stored for key: {args.key}")
                return 0
            else:
                print(f"❌ Failed to store credential for key: {args.key}")
                return 1
                
        elif args.credential_action == "get":
            if not args.key:
                print("❌ --key is required for getting credentials")
                return 1
            
            value = credential_manager.get_credential(args.key)
            if value:
                print(value)
                return 0
            else:
                print(f"❌ Credential not found for key: {args.key}")
                return 1
                
        elif args.credential_action == "delete":
            if not args.key:
                print("❌ --key is required for deleting credentials")
                return 1
            
            if credential_manager.delete_credential(args.key):
                print(f"✅ Credential deleted for key: {args.key}")
                return 0
            else:
                print(f"❌ Failed to delete credential for key: {args.key}")
                return 1
        
    except Exception as e:
        print(f"❌ Error managing credential: {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="EFIS Data Manager Configuration CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate configuration
  python -m shared.config.config_cli validate

  # Create new configuration
  python -m shared.config.config_cli create --output config/my_config.yaml

  # Show current configuration
  python -m shared.config.config_cli show --format json

  # Set configuration value
  python -m shared.config.config_cli set windows.syncInterval 1800

  # Get configuration value
  python -m shared.config.config_cli get macos.archivePath

  # Manage credentials
  python -m shared.config.config_cli credential set --key email_password --value mypassword
  python -m shared.config.config_cli credential get --key email_password
        """
    )
    
    # Global options
    parser.add_argument(
        "--config", "-c",
        help="Configuration file path"
    )
    parser.add_argument(
        "--environment", "-e",
        choices=["development", "staging", "production"],
        help="Environment name"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate configuration")
    validate_parser.set_defaults(func=validate_config_command)
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create new configuration")
    create_parser.add_argument("--output", "-o", required=True, help="Output file path")
    create_parser.add_argument("--force", "-f", action="store_true", help="Overwrite existing file")
    create_parser.set_defaults(func=create_config_command)
    
    # Migrate command
    migrate_parser = subparsers.add_parser("migrate", help="Migrate configuration")
    migrate_parser.add_argument("--output", "-o", help="Output file path (default: migrate in place)")
    migrate_parser.set_defaults(func=migrate_config_command)
    
    # Show command
    show_parser = subparsers.add_parser("show", help="Display configuration")
    show_parser.add_argument("--format", choices=["yaml", "json"], default="yaml", help="Output format")
    show_parser.set_defaults(func=show_config_command)
    
    # Set command
    set_parser = subparsers.add_parser("set", help="Set configuration value")
    set_parser.add_argument("key", help="Configuration key (dot notation)")
    set_parser.add_argument("value", help="Configuration value")
    set_parser.set_defaults(func=set_config_command)
    
    # Get command
    get_parser = subparsers.add_parser("get", help="Get configuration value")
    get_parser.add_argument("key", help="Configuration key (dot notation)")
    get_parser.add_argument("--format", choices=["yaml", "json"], default="yaml", help="Output format")
    get_parser.set_defaults(func=get_config_command)
    
    # Credential command
    credential_parser = subparsers.add_parser("credential", help="Manage secure credentials")
    credential_parser.add_argument("credential_action", choices=["set", "get", "delete"], help="Credential action")
    credential_parser.add_argument("--key", help="Credential key")
    credential_parser.add_argument("--value", help="Credential value (for set action)")
    credential_parser.set_defaults(func=credential_command)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())