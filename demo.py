import tkinter as tk
from tkinter import messagebox
import chess
import chess.engine
from PIL import Image, ImageTk

PIECE_VALUES = {
    "p": 1,
    "n": 3,
    "b": 3,
    "r": 5,
    "q": 9,
    "k": 0
}

class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chess Game")
        
        # Set a larger window size
        self.root.geometry("800x800")  # Adjust window size
        
        # Configure grid to expand frames properly
        self.root.grid_rowconfigure(0, weight=1)  # Make row 0 expand
        self.root.grid_columnconfigure(0, weight=1)  # Make column 0 expand
        self.root.grid_columnconfigure(1, weight=2)  # Make column 1 expand more (for the board)
        self.root.grid_columnconfigure(2, weight=1)  # Make column 2 expand
        self.root.grid_rowconfigure(1, weight=0)  # Make row 1 fixed size (for the bottom info section)
        
        self.board = chess.Board()

        # Frame Setup
        self.left_frame = tk.Frame(self.root)
        self.left_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.center_frame = tk.Frame(self.root)
        self.center_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        self.right_frame = tk.Frame(self.root)
        self.right_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")

        self.bottom_frame = tk.Frame(self.root)
        self.bottom_frame.grid(row=1, column=1, pady=5, sticky="nsew")

        # Ensure bottom_frame expands properly
        self.bottom_frame.grid_rowconfigure(0, weight=1)  # Center the info section
        self.bottom_frame.grid_rowconfigure(1, weight=0)  # Fixed size for the button row
        self.bottom_frame.grid_columnconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(1, weight=1)

        # Canvas setup (keep the canvas size the same or modify as needed)
        self.margin = 20
        self.square_size = 60  # Increased square size for a larger board
        canvas_size = 8 * self.square_size + 2 * self.margin
        self.canvas = tk.Canvas(self.center_frame, width=canvas_size, height=canvas_size, bg="saddlebrown", highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_square_click)

        # Captured pieces
        self.captured_white_frame = tk.Frame(self.left_frame)
        self.captured_white_frame.pack()

        self.captured_black_frame = tk.Frame(self.right_frame)
        self.captured_black_frame.pack()

        # Info section under board
        self.info_left = tk.Frame(self.bottom_frame)
        self.info_left.grid(row=0, column=0, padx=10, sticky="nsew")

        self.info_right = tk.Frame(self.bottom_frame)
        self.info_right.grid(row=0, column=1, padx=10, sticky="nsew")

        # Pawn advantage icon
        self.advantage_pawn_label = tk.Label(self.info_left)
        self.advantage_pawn_label.pack()

        # Material score
        self.material_label = tk.Label(self.info_left, text="Material: Even", font=("Arial", 12, "bold"))
        self.material_label.pack(pady=(45, 5))  # Lower the material label height by adjusting padding

        # Move history with scrollbar
        self.scrollbar = tk.Scrollbar(self.info_right)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.move_history = tk.Text(self.info_right, height=10, width=20, font=("Courier", 10), yscrollcommand=self.scrollbar.set)
        self.move_history.pack()
        self.move_history.config(state="disabled")
        self.scrollbar.config(command=self.move_history.yview)

        # Center the restart button under move history
        self.restart_button = tk.Button(self.bottom_frame, text="Restart", command=self.restart_game, font=("Arial", 12))
        self.restart_button.grid(row=1, column=0, columnspan=2, pady=10, sticky="nsew")  # Ensure it spans both columns and is centered




        # Load resources
        self.board_images = self.load_images()
        self.piece_images_on_canvas = {}
        self.selected_square = None
        self.legal_destinations = []
        self.last_move = None

        # Game tracking
        self.captured_white = []
        self.captured_black = []

        # Engine
        self.stockfish = self.init_stockfish()

        self.draw_board()



    def load_images(self):
        images = {}
        pieces = ["k", "q", "r", "b", "n", "p"]
        for color in ["w", "b"]:
            for piece in pieces:
                name = f"{color}{piece}"
                try:
                    image = Image.open(f"images/{name}.png")
                    images[name] = image
                except FileNotFoundError:
                    print(f"Missing image: images/{name}.png")
        return images

    def init_stockfish(self):
        engine = chess.engine.SimpleEngine.popen_uci("stockfish/stockfish.exe")
        engine.configure({
            "UCI_LimitStrength": True,
            "UCI_Elo": 1320  # Adjust this number to change difficulty (e.g., 800–2850)
        })
        return engine

    def piece_type_to_name(self, piece_type, color):
        mapping = {1: 'p', 2: 'n', 3: 'b', 4: 'r', 5: 'q', 6: 'k'}
        return f"{'w' if color else 'b'}{mapping[piece_type]}"

    def draw_board(self):
        self.canvas.delete("all")
        for row in range(8):
            for col in range(8):
                x1 = self.margin + col * self.square_size
                y1 = self.margin + row * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size
                square = chess.square(col, 7 - row)

                color = "white" if (row + col) % 2 == 0 else "gray"
                if self.selected_square is not None and square in self.legal_destinations:
                    color = "#ADD8E6"
                elif self.last_move:
                    if square == self.last_move.from_square:
                        color = "#FFFFCC"
                    elif square == self.last_move.to_square:
                        color = "#CCFFCC"

                if self.board.is_check():
                    king_square = self.board.king(self.board.turn)
                    if square == king_square:
                        color = "#FF6666"

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="black")

                piece = self.board.piece_at(square)
                if piece:
                    name = self.piece_type_to_name(piece.piece_type, piece.color)
                    image = self.board_images.get(name)
                    if image:
                        img = image.resize((self.square_size, self.square_size))
                        img_tk = ImageTk.PhotoImage(img)
                        self.piece_images_on_canvas[square] = img_tk
                        self.canvas.create_image(x1 + self.square_size // 2, y1 + self.square_size // 2, image=img_tk)

        self.draw_coordinates()

    def draw_coordinates(self):
        files = 'abcdefgh'
        ranks = '87654321'
        for i in range(8):
            x = self.margin + i * self.square_size + self.square_size // 2
            y = self.margin // 2
            self.canvas.create_text(x, y, text=files[i], font=("Arial", 10, "bold"))

            x = self.margin // 2
            y = self.margin + i * self.square_size + self.square_size // 2
            self.canvas.create_text(x, y, text=ranks[i], font=("Arial", 10, "bold"))

    def on_square_click(self, event):
        col = (event.x - self.margin) // self.square_size
        row = (event.y - self.margin) // self.square_size
        if not (0 <= col < 8 and 0 <= row < 8):
            return
        square = chess.square(col, 7 - row)
        if self.selected_square == square:
            self.selected_square = None
            self.legal_destinations.clear()
            self.draw_board()
            return
        if self.selected_square is None:
            piece = self.board.piece_at(square)
            if piece and piece.color == self.board.turn:
                self.selected_square = square
                self.legal_destinations = [move.to_square for move in self.board.legal_moves if move.from_square == square]
        else:
            move = chess.Move(self.selected_square, square)
            if move in self.board.legal_moves:
                self.last_move = move
                captured = self.board.piece_at(move.to_square)
                if captured:
                    self.record_capture(captured)
                self.board.push(move)
                self.selected_square = None
                self.legal_destinations.clear()
                self.animate_move(move)
                self.update_move_history()
                if self.board.is_check():
                    self.root.after(100, lambda: messagebox.showinfo("Check", "Check!"))
                if self.board.is_game_over():
                    self.show_game_over()
                else:
                    self.root.after(500, self.ai_turn)
            else:
                self.selected_square = None
                self.legal_destinations.clear()
        self.draw_board()

    def ai_turn(self):
        if self.board.is_game_over():
            self.show_game_over()
            return
        result = self.stockfish.play(self.board, chess.engine.Limit(time=.025))
        move = result.move
        self.last_move = move
        captured = self.board.piece_at(move.to_square)
        if captured:
            self.record_capture(captured)
        self.board.push(move)
        self.selected_square = None
        self.legal_destinations.clear()
        self.animate_move(move)
        self.update_move_history()
        if self.board.is_check():
            self.root.after(100, lambda: messagebox.showinfo("Check", "Check!"))
        if self.board.is_game_over():
            self.show_game_over()

    def animate_move(self, move, steps=10, delay=2):
        piece = self.board.piece_at(move.to_square)
        if not piece:
            self.draw_board()
            return
        from_col = chess.square_file(move.from_square)
        from_row = 7 - chess.square_rank(move.from_square)
        to_col = chess.square_file(move.to_square)
        to_row = 7 - chess.square_rank(move.to_square)
        dx = (to_col - from_col) * self.square_size / steps
        dy = (to_row - from_row) * self.square_size / steps
        name = self.piece_type_to_name(piece.piece_type, piece.color)
        image = self.board_images.get(name)
        image = image.resize((self.square_size, self.square_size))
        img_tk = ImageTk.PhotoImage(image)
        def step(i):
            self.draw_board()
            x = self.margin + from_col * self.square_size + dx * i + self.square_size // 2
            y = self.margin + from_row * self.square_size + dy * i + self.square_size // 2
            self.canvas.create_image(x, y, image=img_tk)
            self.canvas.image = img_tk
            if i < steps:
                self.root.after(delay, step, i + 1)
            else:
                self.draw_board()
        step(0)

    def record_capture(self, captured_piece):
        piece_name = self.piece_type_to_name(captured_piece.piece_type, captured_piece.color)
        if captured_piece.color == chess.WHITE:
            self.captured_black.append(piece_name)
        else:
            self.captured_white.append(piece_name)
        self.check_captures()

    def update_captured_pieces(self, frame, captured_pieces, is_white=True):
        for widget in frame.winfo_children():
            widget.destroy()

    # Determine the placement based on whether it is white or black
        for i, piece in enumerate(captured_pieces):
            image = self.board_images.get(piece)
            if image:
                img = image.resize((40, 40))
                img_tk = ImageTk.PhotoImage(img)
                label = tk.Label(frame, image=img_tk)
                label.image = img_tk
                if is_white:  # For white pieces, place them from top-left
                    label.grid(row=i, column=0, padx=5, pady=5)
                else:  # For black pieces, place them from bottom-right
                    label.grid(row=i, column=0, padx=5, pady=5)


    def check_captures(self):
        white_value = sum([PIECE_VALUES[p[1:]] for p in self.captured_white])
        black_value = sum([PIECE_VALUES[p[1:]] for p in self.captured_black])
        diff = white_value - black_value
        if diff > 0:
            self.material_label.config(text=f"Material: White +{diff}")
            pawn_img = self.board_images.get("wp")
        elif diff < 0:
            self.material_label.config(text=f"Material: Black +{abs(diff)}")
            pawn_img = self.board_images.get("bp")
        else:
            self.material_label.config(text="Material: Even")
            pawn_img = None
        if pawn_img:
            pawn_img = pawn_img.resize((50, 50))
            pawn_tk = ImageTk.PhotoImage(pawn_img)
            self.advantage_pawn_label.config(image=pawn_tk)
            self.advantage_pawn_label.image = pawn_tk
        else:
            self.advantage_pawn_label.config(image='')

    # Update captured pieces with the correct placement
        self.update_captured_pieces(self.captured_white_frame, self.captured_white, is_white=True)
        self.update_captured_pieces(self.captured_black_frame, self.captured_black, is_white=False)


    def update_move_history(self):
        self.move_history.config(state="normal")
        self.move_history.delete(1.0, tk.END)
        moves = list(self.board.move_stack)
        temp_board = chess.Board()
        for i in range(0, len(moves), 2):
            white = temp_board.san(moves[i])
            temp_board.push(moves[i])
            black = ""
            if i + 1 < len(moves):
                black = temp_board.san(moves[i + 1])
                temp_board.push(moves[i + 1])
            self.move_history.insert(tk.END, f"{(i // 2) + 1}. {white:6} {black:6}\n")
        self.move_history.config(state="disabled")
        self.move_history.see(tk.END)
        self.check_captures()

    def show_game_over(self):
        result = "Draw"
        if self.board.result() == "1-0":
            result = "White wins!"
        elif self.board.result() == "0-1":
            result = "Black wins!"
        messagebox.showinfo("Game Over", f"Game over: {result}")

    def restart_game(self):
        self.board.reset()
        self.selected_square = None
        self.legal_destinations.clear()
        self.last_move = None
        self.captured_white = []
        self.captured_black = []
        self.move_history.config(state="normal")
        self.move_history.delete(1.0, tk.END)
        self.move_history.config(state="disabled")
        self.material_label.config(text="Material: Even")
        self.advantage_pawn_label.config(image='')
        self.draw_board()
        self.update_captured_pieces(self.captured_white_frame, self.captured_white)
        self.update_captured_pieces(self.captured_black_frame, self.captured_black)

def main():
    root = tk.Tk()
    game = ChessGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
