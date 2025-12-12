"""
MCP Toolbox Wrapper
Simplified interface to call tools defined in tools.yaml
"""

import logging
from typing import Dict, Any
# from dotenv import load_dotenv
# load_dotenv()

from dotenv import load_dotenv
import os
load_dotenv()
CLIENT_URL = os.getenv("CLIENT_URL", "https://toolbox-service-440584682160.us-central1.run.app")

# FIXED IMPORT (THIS IS THE REAL CLIENT FOR YOUR TOOLBOX)
from toolbox_core import ToolboxSyncClient

logger = logging.getLogger(__name__)


class ToolboxWrapper:
    """Wrapper for MCP Toolbox client"""

    def __init__(self, toolbox_url: str = CLIENT_URL):
        self.toolbox_url = toolbox_url
        self.client = None
        self.tools = None
        self._initialize()
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.close()
    
    def close(self):
        """Close the client connection properly"""
        if self.client:
            try:
                self.client.close()
            except Exception as e:
                logger.warning(f"Error closing toolbox client: {e}")

    def _initialize(self):
        """Initialize connection to toolbox"""
        try:
            logger.info(f"Connecting to MCP Toolbox at {self.toolbox_url}")

            # Create MCP Toolbox client
            self.client = ToolboxSyncClient(self.toolbox_url)

            # Load toolset (try without arguments first, which loads the default toolset)
            try:
                self.tools = self.client.load_toolset()
                logger.info("✅ Loaded tools from toolbox (default toolset)")
            except Exception as e:
                # Fallback: try loading "default" explicitly
                logger.warning(f"Failed to load toolset without args, trying 'default': {e}")
                self.tools = self.client.load_toolset("default")
                logger.info("✅ Loaded tools from 'default' toolset")

        except TimeoutError as e:
            error_msg = (
                f"❌ Toolbox connection timeout. "
                f"Make sure the toolbox server is running:\n"
                f"   cd mcp_toolbox && ./toolbox --tools-file tools.yaml"
            )
            logger.error(error_msg)
            raise ConnectionError(error_msg) from e
        except Exception as e:
            logger.error(f"❌ Failed to initialize toolbox: {e}")
            raise

    def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Call tool defined in tools.yaml"""
        try:
            logger.info(f"Calling tool: {tool_name} with params {kwargs}")

            # Load the specific tool and call it
            tool = self.client.load_tool(tool_name)
            result = tool(**kwargs)

            return {
                "success": True,
                "data": result,
                "rows": result if isinstance(result, list) else []
            }

        except Exception as e:
            logger.error(f"❌ Tool call failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": None,
                "rows": []
            }


# GLOBAL INSTANCE
_toolbox = None

def get_toolbox() -> ToolboxWrapper:
    global _toolbox
    if _toolbox is None:
        _toolbox = ToolboxWrapper()
    return _toolbox
