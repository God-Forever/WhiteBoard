# WhiteBoard

A lightweight screen annotation tool based on PySide6, featuring a floating control ball, freehand drawing, and a web whiteboard.

## 📥 Installation

### Option 1: Pre-built Release (Recommended)

1.  Download the **`WhiteBoard.zip`** from the [Releases](https://github.com/God-Forever/WhiteBoard/releases) page.
2.  Unzip the file to any directory.
3.  Double-click **`reg.exe`** to add the program to the Windows Registry (this sets up necessary configurations).

### Option 2: Run from Source

**Prerequisites:**
*   Windows OS
*   Python 3.10+

**Steps:**

```bash
git clone https://github.com/God-Forever/WhiteBoard.git
cd WhiteBoard
pip install pyside6 pyside6
python WhiteBoard.pyw
```
## 🎮 Usage

Upon launching, a **Floating Ball** will appear in the top-right corner of your screen.

### 1. Floating Ball (Screen Annotation)

The floating ball allows you to draw directly on your screen over other applications.

| Button | Icon | Action |
| :--- | :--- | :--- |
| **Top** | 📄 Paper | **Open/Close** the Web Whiteboard window. |
| **Middle** | ✏️ Pen | **Expand/Collapse** the control panel. |
| **Bottom** | 🗑️ Trash | **Clear** the entire screen canvas. |

**Expanded Panel Controls:**

*   **Mouse Mode**: Mouse clicks pass through to underlying windows.
*   **Pen Mode**: Draw on the screen. Adjustable thickness and colors.
*   **Eraser Mode**: Remove strokes.

### 2. Web Whiteboard (Advanced Editing)

Click the **Paper icon** (Top button) on the floating ball to open the Web Whiteboard. This is a full-featured whiteboard interface loaded via `QWebEngineView`.

**Key Features:**

*   **Large  Canvas & Multi-Page**:
    *   Add or delete pages dynamically.
    *   Navigate via page dots on the right side.
*   **Rich Drawing Tools**:
    *   **Pen**: Customizable thickness and colors. Supports dynamic colors (e.g., color inverts based on background).
    *   **Eraser**: With adjustable size.
    *   **Move Tool**: Pan and navigate across the large canvas.
*   **History Management**:
    *   **Undo/Redo**: Supports keyboard shortcuts (`Ctrl+Z` / `Ctrl+Shift+Z`).
    *   **Clear**: Clear the current page instantly.
*   **Customization**:
    *   **Background Colors**: Choose from 12 preset background colors (including dark modes).
    *   **Dynamic Color Modes**: Invert color mode automatically adjusts pen color for visibility against the background.
