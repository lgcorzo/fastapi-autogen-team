# US [Data Model](./backlog_mlops_regresion.md) : Define structured data formats for AI/ML pipeline.

- [US Data Model : Define structured data formats for AI/ML pipeline.](#us-data-model--define-structured-data-formats-for-aiml-pipeline)
  - [classes relations](#classes-relations)
  - [**User Stories: Data Model Management**](#user-stories-data-model-management)
    - [**1. User Story: Define Model Information Schema**](#1-user-story-define-model-information-schema)
    - [**2. User Story: Define Message Schema**](#2-user-story-define-message-schema)
    - [**3. User Story: Define Input Schema**](#3-user-story-define-input-schema)
    - [**4. User Story: Define Output Schema**](#4-user-story-define-output-schema)
    - [**Common Acceptance Criteria**](#common-acceptance-criteria)
    - [**Definition of Done (DoD):**](#definition-of-done-dod)
  - [Code location](#code-location)
  - [Test location](#test-location)

------------

## classes relations

``` mermaid

classDiagram
  class ModelInformation {
    +id: str
    +name: str
    +description: str
    +pricing: dict
    +context_length: int
    +architecture: dict
    +top_provider: dict
    +per_request_limits: Optional[dict]
  }
  class Message {
    +role: str
    +content: str
  }
  class Input {
    +model: str
    +messages: List[Message]
    +temperature: float = 1
    +top_p: float = 1
    +presence_penalty: float = 0
    +frequency_penalty: float = 0
    +stream: bool = True
  }
  class Output {
    +id: str
    +object: str = "chat.completion"
    +created: int
    +model: str
    +choices: List
    +usage: dict
  }
  ModelInformation --|> BaseModel : extends
  Message --|> BaseModel : extends
  Input --|> BaseModel : extends
  Output --|> BaseModel : extends
  Input -- Message : contains

```

## **User Stories: Data Model Management**

---

### **1. User Story: Define Model Information Schema**

**Title:** As a **data scientist**, I want to define a schema for model information that includes details such as ID, name, description, pricing, context length, architecture, top provider, and request limits, so that I can manage and track different models effectively.

**Description:** The `ModelInformation` class provides a structured way to store and manage metadata about available models, ensuring consistency and facilitating model selection and tracking.

**Acceptance Criteria:**

- The `ModelInformation` class includes fields for:
  - `id` (str): A unique identifier for the model.
  - `name` (str): The name of the model.
  - `description` (str): A description of the model.
  - `pricing` (dict): Pricing information for using the model.
  - `context_length` (int): The context length supported by the model.
  - `architecture` (dict): The model architecture details.
  - `top_provider` (dict): Information about the model provider.
  - `per_request_limits` (Optional[dict]): Limits on requests to the model.
- All fields are properly typed using Pydantic.
- The schema is validated to ensure data integrity.

---

### **2. User Story: Define Message Schema**

**Title:** As a **developer**, I want to define a schema for messages exchanged between the user and the model, so that I can standardize the format of conversations.

**Description:** The `Message` class provides a structured way to represent messages, including the role of the sender and the content of the message.

**Acceptance Criteria:**

- The `Message` class includes fields for:
  - `role` (str): The role of the message sender (e.g., "user", "assistant").
  - `content` (str): The content of the message.
- All fields are properly typed using Pydantic.
- The schema is validated to ensure data integrity.

---

### **3. User Story: Define Input Schema**

**Title:** As a **developer**, I want to define a schema for input data sent to the model, including model selection, messages, and generation parameters, so that I can ensure consistent and valid input.

**Description:** The `Input` class provides a structured way to represent input data sent to the model for generating responses.

**Acceptance Criteria:**

- The `Input` class includes fields for:
  - `model` (str): The name of the model to use.
  - `messages` (List[Message]): A list of messages in the conversation.
  - `temperature` (float, default=1): The sampling temperature.
  - `top_p` (float, default=1): The nucleus sampling probability.
  - `presence_penalty` (float, default=0): The presence penalty.
  - `frequency_penalty` (float, default=0): The frequency penalty.
  - `stream` (bool, default=True): Whether to stream the response.
- All fields are properly typed using Pydantic.
- Default values are provided for optional parameters.
- The schema is validated to ensure data integrity.

---

### **4. User Story: Define Output Schema**

**Title:** As a **developer**, I want to define a schema for output data received from the model, including ID, object type, creation timestamp, model used, choices, and usage statistics, so that I can standardize the format of responses.

**Description:** The `Output` class provides a structured way to represent the output data received from the model.

**Acceptance Criteria:**

- The `Output` class includes fields for:
  - `id` (str): A unique identifier for the output.
  - `object` (str, default="chat.completion"): The type of object (always "chat.completion").
  - `created` (int): The creation timestamp of the output.
  - `model` (str): The name of the model used.
  - `choices` (List): A list of choices generated by the model.
  - `usage` (dict): Usage statistics (e.g., token counts).
- All fields are properly typed using Pydantic.
- Default values are provided for optional parameters.
- The schema is validated to ensure data integrity.

---

### **Common Acceptance Criteria**

1. **Implementation Requirements:**
   - All classes inherit from `pydantic.BaseModel`.
   - All fields are correctly type-annotated.
   - Default values are specified where appropriate.

2. **Validation:**
   - Pydantic's validation mechanisms are used to ensure data integrity.
   - Validation errors are raised for invalid data.

3. **Extensibility:**
   - The classes are designed to be extensible, allowing for future addition of new fields or modifications of existing ones.

4. **Documentation:**
   - Clear docstrings are provided for all classes and fields.

---

### **Definition of Done (DoD):**

- All classes (`ModelInformation`, `Message`, `Input`, `Output`) are implemented with clear documentation.
- All fields are properly typed and validated.
- Unit tests cover the creation of valid and invalid objects.
- Code adheres to the project's coding standards and passes peer review.

## Code location

[src/fastapi_autogen_team/data_model.py](../src/fastapi_autogen_team/data_model.py)

## Test location

[tests/test_data_model.py](../tests/test_data_model.py)
