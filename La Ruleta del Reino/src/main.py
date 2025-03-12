import flet as ft
import unicodedata

def main(page: ft.Page):
    # Set the app title and properties
    page.title = "La Ruleta del Reino"
    page.padding = 20
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.Colors.BLUE_50
    
    # Store the original phrase and game state
    original_phrase = ""
    pending_reveals = []  # List to store positions of letters waiting to be revealed
    
    # Set default panel dimensions
    letter_width = 40
    max_chars_per_row = 12
    
    # Helper function to normalize Spanish letters (remove accents for comparison)
    def normalize_letter(letter):
        # Normalize to NFD form to separate base character and accent
        normalized = unicodedata.normalize('NFD', letter)
        # Keep only the base character (removing combining marks)
        base_letter = ''.join([c for c in normalized if not unicodedata.combining(c)])
        # Special case for ñ which should remain ñ (not n)
        if letter.lower() == 'ñ':
            return 'ñ'
        return base_letter
    
    # Function to check if two letters match, ignoring accents
    def letters_match(letter1, letter2):
        return normalize_letter(letter1.upper()) == normalize_letter(letter2.upper())
    
    # Function to handle button click and create panel
    def create_panel(e):
        # Clear any existing panel
        panel_container.content = None
        
        phrase = phrase_input.value.upper()  # Convert to uppercase
        if not phrase:
            return
            
        # Store the original phrase for later validation
        nonlocal original_phrase
        original_phrase = phrase
        
        # Clear any pending reveals
        nonlocal pending_reveals
        pending_reveals = []
        
        rows = []
        current_row = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=2)
        chars_in_row = 0
        
        # Split the phrase into words
        words = phrase.split()
        
        # Process each word
        i = 0
        while i < len(words):
            word = words[i]
            
            # Check if this word would exceed the line width
            if chars_in_row + len(word) > max_chars_per_row:
                # If the word alone exceeds the max width, it must be placed on a new line
                if chars_in_row == 0:
                    # Add each character of this long word
                    for char in word:
                        # Add the character
                        create_character_container(current_row, char)
                        chars_in_row += 1
                        
                        # Start a new row if needed
                        if chars_in_row >= max_chars_per_row and char != word[-1]:
                            rows.append(current_row)
                            current_row = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=2)
                            chars_in_row = 0
                    
                    # Add a space after the word (unless it's the last word)
                    if i < len(words) - 1:
                        create_character_container(current_row, ' ')
                        chars_in_row += 1
                else:
                    # If we already have content on this line, start a new line
                    rows.append(current_row)
                    current_row = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=2)
                    chars_in_row = 0
                    # Don't increment i, we'll process this word on the new line
                    continue
            else:
                # Add each character of the word
                for char in word:
                    create_character_container(current_row, char)
                    chars_in_row += 1
                
                # Add a space after the word (unless it's the last word)
                if i < len(words) - 1:
                    create_character_container(current_row, ' ')
                    chars_in_row += 1
            
            i += 1
        
        # Add the last row if it has any controls
        if current_row.controls:
            rows.append(current_row)
        
        # Place rows in a column
        panel_container.content = ft.Column(rows, alignment=ft.MainAxisAlignment.CENTER, spacing=10)
        
        # Switch to guess mode
        setup_container.visible = False
        guess_container.visible = True
        
        # Initialize button for "Adivinar"
        reset_guess_button()
        
        page.update()
    
    # Helper function to create character containers
    def create_character_container(row, char):
        if char == ' ':
            # Handle spaces - add a transparent container with a special data property
            row.controls.append(
                ft.Container(
                    width=letter_width,
                    height=letter_width * 1.5,
                    margin=2,
                    bgcolor=ft.Colors.TRANSPARENT,
                    data="SPACE",  # Mark this as a space container
                )
            )
        else:
            # Determine if it's a special character
            is_special = not char.isalnum()
            
            # Create a rectangle for each letter
            row.controls.append(
                ft.Container(
                    width=letter_width,
                    height=letter_width * 1.5,
                    margin=2,
                    bgcolor=ft.Colors.WHITE,
                    border=ft.border.all(2, ft.Colors.BLUE_800),
                    border_radius=5,
                    alignment=ft.alignment.center,
                    content=ft.Text(
                        # Show special characters immediately, hide others
                        value=char if is_special else "",
                        size=int(letter_width * 0.6),
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLACK,
                    ),
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=4,
                        color=ft.Colors.BLUE_GREY_300,
                        offset=ft.Offset(2, 2)
                    ),
                    data="NORMAL",  # Initial state
                )
            )
    
    # Function to apply the yellow highlight effect (without revealing letter)
    def apply_highlight_effect(container, letter, position):
        # Create a subtle yellow effect
        container.bgcolor = "#FFF176"  # Light yellow color
        
        # Add a gentle glow effect
        container.shadow = ft.BoxShadow(
            spread_radius=1,
            blur_radius=6,
            color="#FFD54F80",  # Yellow with opacity
            offset=ft.Offset(0, 0)
        )
        
        # Store the letter to be revealed later but don't show it yet
        if container.content and isinstance(container.content, ft.Text):
            container.content.value = ""  # Keep it blank for now
            container.data = f"PENDING:{letter}"  # Mark as pending reveal with the letter
            
        # Add this position to our queue of letters to reveal
        nonlocal pending_reveals
        pending_reveals.append(position)
    
    # Function to restore the original appearance of a container while showing the letter
    def restore_original_appearance(container, letter):
        # Reset to original styling
        container.bgcolor = ft.Colors.WHITE
        container.border = ft.border.all(2, ft.Colors.BLUE_800)
        container.border_radius = 5
        container.shadow = ft.BoxShadow(
            spread_radius=1,
            blur_radius=4,
            color=ft.Colors.BLUE_GREY_300,
            offset=ft.Offset(2, 2)
        )
        
        # Show the letter
        if container.content and isinstance(container.content, ft.Text):
            container.content.value = letter
            
        # Mark as revealed
        container.data = "REVEALED"
    
    # Function to reveal the next pending letter
    def reveal_next_letter():
        # Check if there are any letters to reveal
        nonlocal pending_reveals
        if not pending_reveals:
            return False
        
        # Get the position of the next letter to reveal
        next_position = pending_reveals.pop(0)
        row_index, container_index = next_position
        
        # Find the container at this position
        if panel_container.content and len(panel_container.content.controls) > row_index:
            row = panel_container.content.controls[row_index]
            if len(row.controls) > container_index:
                container = row.controls[container_index]
                
                # Extract the letter from the data
                if hasattr(container, "data") and isinstance(container.data, str) and container.data.startswith("PENDING:"):
                    letter = container.data.split(":", 1)[1]
                    
                    # Restore original appearance and show letter
                    restore_original_appearance(container, letter)
                    return True
        
        return False
    
    # Function to reveal all letters in the panel
    def reveal_all_letters(e):
        if not panel_container.content or not original_phrase:
            return
            
        phrase_index = 0  # Index in the original phrase
        
        for row in panel_container.content.controls:
            for container in row.controls:
                # Skip space containers (transparent ones)
                if hasattr(container, "data") and container.data == "SPACE":
                    phrase_index += 1
                    continue
                    
                # For letter containers that aren't already revealed
                if container.content and isinstance(container.content, ft.Text):
                    if phrase_index < len(original_phrase) and container.content.value == "":
                        # Restore original appearance and reveal the letter
                        restore_original_appearance(container, original_phrase[phrase_index])
                
                # Increment our index in the original phrase
                phrase_index += 1
        
        # Clear any pending reveals
        nonlocal pending_reveals
        pending_reveals = []
        
        # Reset button to "Adivinar" mode
        reset_guess_button()
        
        page.update()
    
    # Function to reset the guess button to "Adivinar" mode
    def reset_guess_button():
        nonlocal pending_reveals
        pending_reveals = []
        guess_button.text = "Adivinar"
        guess_button.icon = ft.Icons.CHECK_CIRCLE
        guess_button.style = ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.GREEN,
        )
        guess_button.on_click = guess_letter
        page.update()
    
    # Function to handle letter guessing or revealing next letter
    def guess_letter(e):
        # If there are pending letters to reveal, reveal the next one
        nonlocal pending_reveals
        if pending_reveals:
            reveal_next_letter()
            
            # If no more pending letters, reset button
            if not pending_reveals:
                reset_guess_button()
                
            page.update()
            return
        
        letter = guess_input.content.value.upper()
        if not letter or len(letter) != 1:
            return
            
        # Check for matches and highlight them
        if panel_container.content:
            phrase_index = 0  # Index in the original phrase
            found_match = False
            
            # First, store positions of all matches
            matches = []
            row_index = 0
            
            for row in panel_container.content.controls:
                container_index = 0
                for container in row.controls:
                    # Skip space containers (transparent ones)
                    if hasattr(container, "data") and container.data == "SPACE":
                        phrase_index += 1
                        container_index += 1
                        continue
                        
                    # Skip already revealed or pending containers
                    if hasattr(container, "data") and (container.data == "REVEALED" or 
                                                      (isinstance(container.data, str) and 
                                                       container.data.startswith("PENDING:"))):
                        phrase_index += 1
                        container_index += 1
                        continue
                    
                    # For regular letter containers
                    if container.content and isinstance(container.content, ft.Text):
                        # Check if this letter matches the guessed letter, ignoring accents
                        if phrase_index < len(original_phrase) and letters_match(original_phrase[phrase_index], letter):
                            # Store this match for later processing
                            matches.append((row_index, container_index, original_phrase[phrase_index]))
                            found_match = True
                    
                    # Increment indices
                    phrase_index += 1
                    container_index += 1
                
                row_index += 1
            
            # Now process all matches - apply highlight effect
            for match in matches:
                row_index, container_index, original_letter = match
                row = panel_container.content.controls[row_index]
                container = row.controls[container_index]
                # Use the original letter from the phrase (preserving accents)
                apply_highlight_effect(container, original_letter, (row_index, container_index))
            
            # If any matches were found, change button to "Siguiente"
            if found_match:
                guess_button.text = "Siguiente"
                guess_button.icon = ft.Icons.ARROW_FORWARD
                guess_button.style = ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.BLUE,
                )
        
        # Clear the guess input for next guess
        guess_input.content.value = ""
        page.update()
    
    # Create UI components
    title = ft.Text(
        value="La Ruleta del Reino", 
        size=36, 
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLUE_700,
        text_align=ft.TextAlign.CENTER
    )
    
    subtitle = ft.Text(
        value="El Panel", 
        size=24, 
        weight=ft.FontWeight.NORMAL,
        color=ft.Colors.BLUE_900,
        text_align=ft.TextAlign.CENTER,
    )
    
    # Initial setup UI
    phrase_input = ft.TextField(
        label="Ingresa una frase en español",
        width=400,
        autofocus=True,
        text_align=ft.TextAlign.CENTER,
        border=ft.InputBorder.OUTLINE,
    )
    
    start_button = ft.ElevatedButton(
        text="Comenzar",
        on_click=create_panel,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.BLUE,
        ),
        icon=ft.Icons.PLAY_ARROW_ROUNDED
    )
    
    # Guess UI - TextField inside a Container for styling
    guess_input = ft.Container(
        width=60,  # Make it square like the panel rectangles
        height=60,
        bgcolor=ft.Colors.WHITE,
        border=ft.border.all(2, ft.Colors.BLUE_800),
        border_radius=5,
        padding=5,
        alignment=ft.alignment.center,
        content=ft.TextField(
            width=40,
            height=50,
            text_align=ft.TextAlign.CENTER,
            max_length=1,
            text_size=24,
            border_color=ft.Colors.TRANSPARENT,
            border_width=0,
            cursor_color=ft.Colors.BLUE,
            content_padding=2,
        ),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=4,
            color=ft.Colors.BLUE_GREY_300,
            offset=ft.Offset(2, 2)
        )
    )
    
    # Button that changes between "Adivinar" and "Siguiente"
    guess_button = ft.ElevatedButton(
        text="Adivinar",
        on_click=guess_letter,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.GREEN,
        ),
        icon=ft.Icons.CHECK_CIRCLE
    )
    
    # Button to solve the entire puzzle
    solve_button = ft.ElevatedButton(
        text="Resolver",
        on_click=reveal_all_letters,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.RED_700,
        ),
        icon=ft.Icons.AUTO_AWESOME
    )
    
    # Container for initial setup (phrase input and start button)
    setup_container = ft.Container(
        content=ft.Column([
            ft.Row([phrase_input], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([start_button], alignment=ft.MainAxisAlignment.CENTER),
        ], spacing=10),
        visible=True,
    )
    
    # Container for guessing (letter input, guess button, and solve button)
    guess_container = ft.Container(
        content=ft.Row([
            guess_input,
            guess_button,
            solve_button  # Added the solve button here
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
        visible=False,
    )
    
    # Container for the panel of letters - made responsive with expand
    panel_container = ft.Container(
        padding=20,
        margin=ft.margin.only(top=20),
        border_radius=10,
        alignment=ft.alignment.center,
        expand=True,  # Allow it to fill available space
    )
    
    # Attribution text - made more visible
    attribution = ft.Text(
        value="App by msiciliag",
        size=14,  # Increased size
        color="#0D47A1CC",  # Blue_700 with higher opacity (80%)
        text_align=ft.TextAlign.CENTER,
        weight="500",  # Medium weight
    )
    
    # Add components to the page
    page.add(
        ft.Column(
            [
                ft.Container(padding=10),
                ft.Row([title], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([subtitle], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(padding=10),
                setup_container,
                guess_container,
                ft.Divider(height=20, color=ft.Colors.BLUE_200),
                panel_container,
                ft.Container(
                    padding=15,
                    margin=ft.margin.only(top=25, bottom=10),  # Increased bottom margin
                    content=ft.Row([attribution], alignment=ft.MainAxisAlignment.CENTER),
                ),
            ],
            spacing=5,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,  # Make column fill the page
        )
    )

    # Make responsive without using window_width
    def page_resize(e):
        # Use available width to determine the phrase input width
        if hasattr(e, "control") and hasattr(e.control, "width"):
            available_width = e.control.width
            if available_width < 600:
                phrase_input.width = min(available_width * 0.8, 400)
            else:
                phrase_input.width = 400
        
        # Update the panel to better fit the screen
        nonlocal letter_width, max_chars_per_row
        
        # Adjust max chars based on mobile vs desktop
        is_mobile = phrase_input.width < 400
        
        # Simpler responsive approach
        letter_width = 35 if is_mobile else 40
        max_chars_per_row = 8 if is_mobile else 12
        
        # If we have a panel and need to recreate it, do it here
        if original_phrase and panel_container.content:
            create_panel(None)
            
        page.update()
    
    # Skip window_width for responsiveness - let the layout adapt naturally
    page.on_resize = page_resize
    
    # Handle keyboard shortcuts for guessing
    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Return" and guess_container.visible:
            guess_letter(None)
            
    page.on_keyboard_event = on_keyboard
    page.update()

ft.app(target=main)