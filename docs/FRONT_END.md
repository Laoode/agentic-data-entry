# UI/UX & Architecture Design Specification
**Project:** Agentic Receipt Processing & Data Entry System
**Tech Stack:** React Native, Expo, Expo Router, Reanimated, Expo Blur, Expo Go, Xcode, MCP (Google Sheets Protocol)
**Target Platform:** iOS (Optimized for iPhone 15 Pro dimensions)

## 1. App Architecture & Routing (Expo Router)
The application relies on a Bottom Tab Navigation structure inside the `(tabs)` directory, containing 3 primary screens.

### 1.1 Bottom Navigation Bar
* **Style:** Floating or sticky bottom bar with heavy blur/glassmorphism background (`expo-blur`).
* **Active State:** Tab icons have an oval/pill-shaped background `#CCFF00` with the icon colored `#000000`.
* **Inactive State:** Icons are colored `#71717A` (zinc) with no background.
* **Tabs:** Home(1), Chat (2), Sheet/Data (3), Profile (4).

### 1.2 Screens Breakdown
**A. Home Page (/index) - The Command Center**
* **Header:** User Avatar (top left), Notification/Status icon (top right). Greeting text (e.g., "Hello, Ryuuky").
* **Hero Section:** Large, inviting text ("How can I help automate your data today?") followed by a prominent Primary CTA Button ("Start Data Entry Agent") utilizing the #CCFF00 accent.
* **Quick Prompts (Horizontal Scroll):** Pill-shaped chips for common zero-shot tasks to reduce cognitive load (e.g., "Scan Receipt", "Sync to Sheets", "Monthly Report", "Manual Entry"). Tapping these routes to /chat with a pre-filled intent.
* **Agentic Automations Section:** A 2-column grid displaying complex workflow cards (e.g., "Batch Processing", "Expense Analysis"). Dark surfaces (#0C0C0E) with distinct icons and brief descriptions.
* **Recently Processed:** A mini-list showing the latest MCP actions (e.g., "Alfamart Receipt Extracted - 10 mins ago") providing a quick bridge to the /sheet reality.

**B. Chat Page (`/chat`) - AI Assistant Interface**
* **Header:** Back button (left), "AI Chat" title (center), Settings hamburger menu (right).
* **Scrollable Content:** * **AI Bubble (Left):** Dark grey surface (`#161618`), text white.
  * **User Bubble (Right):** Accent surface (`#CCFF00`), text black. 
  * **Media Support:** Bubbles must support image rendering (for scanned receipts) with rounded corners.
* **Input Area (Bottom):** * Row of utility icons on the left (camera, gallery, folder).
  * Text input field (pill-shaped, dark surface).
  * Send button on the right with `#CCFF00` background.

**C. Sheet Laporan Page (`/sheet`) - MCP Google Sheets Visualizer**
* **Header:** Back button (left), "Laporan Struk - MCP" title (center), context icons (right).
* **Context:** This screen visualizes data fetched/manipulated via the MCP Google Sheets integration.
* **Content (Data Grid) Tailored with Sheet Connected in Google Sheet**

**D. Profile Page (`/profile`)**
* **Header:** "Profile" title (center).
* **Hero Section:** Circular large Avatar, Username ("Ryuuky"), Email below username.
* **List Menu Section:** Rendered as a distinct card with internal dividers.
  * **Items:** Settings, MCP Connection (shows mini icons of GSheets,GDrive), Activity History, Contact Us, Privacy Policy.
  * **Item Layout:** Icon (left), Title, Chevron Right (right).

---

## 2. Visual DNA & Aesthetic
* **Theme:** Pure Dark Mode.
* **Style:** Industrial-minimalist, high-precision data visualization, "SaaS dashboard" feel translated to mobile.
* **Core Elements:** Deep depth, glassmorphism (`expo-blur`), thin high-contrast borders, strict grid adherence.

---

## 3. Design Tokens

### 3.1 Color Palette
* **Background Global:** `#161618` (Very dark grey/almost black)
* **Surface/Cards:** `#0C0C0E`
* **Accent/Primary (The "Neon"):** `#CCFF00`
* **Text Primary:** `#FFFFFF` or `#D4D4D8` (Zinc-300)
* **Text Secondary:** `#A1A1AA` (Zinc-400)
* **Success/Secondary:** `#16A34A` (Green)
* **Borders:** `#27272A` (Zinc-800) or `rgba(255,255,255,0.1)`

### 3.2 Typography (React Native Specs)
* **Font Family:** `Inter` (Requires `expo-font` setup).
* **Header Titles:** 20px - 24px, Font Weight: '600' (SemiBold).
* **Body Text (Chat/Menu):** 14px, Font Weight: '400' (Regular), Line Height: 22px.
* **Data Grid Text (Table):** 12px, Font Weight: '400' or '500'.
* **Captions/Timestamps:** 11px, Font Weight: '400', Color: Text Secondary.

### 3.3 Spacing & Layout
* **Base Unit:** 4px.
* **Screen Padding:** Horizontal 16px to 20px.
* **Card Padding:** 16px.
* **Border Radius:** * Standard Cards: `16px`
  * Chat Bubbles: `16px` (with asymmetrical corners depending on sender).
  * Buttons/Pills: `9999px` (fully rounded).

---

## 4. Components & Materials (Implementation Details)

### Glassmorphism & Shells
* Use `expo-blur` (`<BlurView intensity={20} tint="dark">`) for floating headers, bottom tabs, and overlay elements.
* **Gradient Borders:** To achieve the "gradient edge" look around cards, wrap a standard `<View>` (background `#0C0C0E`) inside an `expo-linear-gradient` wrapper with a `1px` padding.

### Iconography
* **Library:** Use `@expo/vector-icons` (e.g., Ionicons or MaterialIcons as fallback) or implement custom SVG icons if `iconify` 'Solar' linear set SVG files are provided.
* **Default Size:** `24px` for tab nav and menu lists, `18px`-`20px` for utility buttons.
* **Treatment:** Linear/Outline style.

### Icon Implementation
- **Primary Method:** Use `@expo/vector-icons`.
- **Active Tab Style:** Background View (circle) with `#CCFF00`, Icon color `#000000`.
- **Inactive Tab Style:** Icon color `#71717A`.
- **Specific Icons:** - Home: `solar:home-smile-linear` -> map to `Ionicons: home-outline`
  - Sheets: `solar:document-text-linear` -> map to `MaterialCommunityIcons: table-large`
  - Profile: `solar:user-circle-linear` -> map to `FontAwesome5: user-circle`

## 5. Development Directives for Claude
1. Please structure the Expo Router layout files `_layout.tsx` properly to handle the bottom tabs.
2. Build reusable UI components (e.g., `ChatBubble`, `DataGrid`, `MenuItem`) in a `/components` folder before assembling the screens.
3. Use `StyleSheet.create` or `NativeWind` (if installed) adhering strictly to the color hex codes and spacings above. Do not use generic web CSS.
4. Ensure the `DataGrid` in `/sheet` is heavily optimized for horizontal scrolling and data injection from the MCP layer.