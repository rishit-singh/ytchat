# ytchat
Chat with Youtube using Tinytune.

## API Documentation

This project provides a FastAPI-based backend for interacting with YouTube data using AI-powered chat functionality.

### Endpoints

#### POST /prompt

Sends a prompt to the AI assistant and receives a response.

**Request Body:**
- `input` (string, required): The user's input or question.
- `chat_id` (string, optional): A unique identifier for the chat session.

**Response:**
- `response` (object): The AI-generated response, typically containing YouTube-related information.
- `chat_id` (string): The chat session identifier (either provided or newly generated).

**Example Usage:**
