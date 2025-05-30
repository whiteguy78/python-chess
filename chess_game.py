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
        self.board = chess.Board()

        # Setup frames
        self.left_frame = tk.Frame(self.root)
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="n")

        self.board_frame = tk.Frame(self.root)
        self.board_frame.grid(row=0, column=1, padx=10, pady=10)

        self.right_frame = tk.Frame(self.root)
        self.right_frame.grid(row=0, column=2, padx=10, pady=10, sticky="n")

        self.material_label = tk.Label(self.board_frame, text="Material: Even", font=("Arial", 12, "bold"))
        self.material_label.grid(row=1, column=0, pady=(0, 5))

        self.captured_white_frame = tk.Frame(self.left_frame)
        self.captured_white_frame.grid(row=3, column=0, pady=(0, 5))

        self.captured_black_frame = tk.Frame(self.right_frame)
        self.captured_black_frame.grid(row=3, column=0, pady=(0, 5))

        self.move_history = tk.Text(self.board_frame, height=10, width=15, state="disabled", font=("Courier", 10))
        self.move_history.grid(row=3, column=0, padx=0)

        self.restart_button = tk.Button(self.board_frame, text="Restart", command=self.restart_game, font=("Arial", 12))
        self.restart_button.grid(row=4, column=0, pady=10)

        # Add canvas with brown border
        self.margin = 10
        self.square_size = 50
        board_pixel_size = self.square_size * 8
        self.canvas = tk.Canvas(self.board_frame, width=board_pixel_size + 2 * self.margin,
                                height=board_pixel_size + 2 * self.margin,
                                bg="saddlebrown", highlightthickness=0)
        self.canvas.grid(row=0, column=0)

        self.board_images = self.load_images()
        self.selected_square = None
        self.legal_destinations = []
        self.last_move = None
        self.piece_images_on_canvas = {}

        self.canvas.bind("<Button-1>", self.on_square_click)
        self.stockfish = self.init_stockfish()
        self.draw_board()

        self.captured_white = []
        self.captured_black = []

    def load_images(self):
        images = {}
        pieces = ["k", "q", "r", "b", "n", "p"]
        colors = ["w", "b"]
        for color in colors:
            for piece in pieces:
                name = f"{color}{piece}"
                try:
                    image = Image.open(f"images/{name}.png")
                    images[name] = image
                except FileNotFoundError:
                    print(f"Missing image: images/{name}.png")
        return images

    def init_stockfish(self):
        return chess.engine.SimpleEngine.popen_uci("stockfish/stockfish.exe")

    def piece_type_to_name(self, piece_type, color):
        mapping = {1: 'p', 2: 'n', 3: 'b', 4: 'r', 5: 'q', 6: 'k'}
        return f"{'w' if color else 'b'}{mapping[piece_type]}"

    def draw_board(self):
        self.canvas.delete("all")
        for row in range(8):
            for col in range(8):
                x1 = col * self.square_size + self.margin
                y1 = row * self.square_size + self.margin
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
                        self.canvas.create_image(x1 + self.square_size // 2,
                                                 y1 + self.square_size // 2,
                                                 image=img_tk)

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
                self.legal_destinations = [
                    move.to_square for move in self.board.legal_moves if move.from_square == square
                ]
        else:
            move = chess.Move(self.selected_square, square)
            if move in self.board.legal_moves:
                self.last_move = move
                captured_piece = self.board.piece_at(move.to_square)
                if captured_piece:
                    self.record_capture(captured_piece)
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

        result = self.stockfish.play(self.board, chess.engine.Limit(time=2.0))
        move = result.move
        self.last_move = move
        captured_piece = self.board.piece_at(move.to_square)
        if captured_piece:
            self.record_capture(captured_piece)
        self.board.push(move)
        self.selected_square = None
        self.legal_destinations.clear()
        self.animate_move(move)
        self.update_move_history()

        if self.board.is_check():
            self.root.after(100, lambda: messagebox.showinfo("Check", "Check!"))

        if self.board.is_game_over():
            self.show_game_over()

    def record_capture(self, captured_piece):
        piece_name = self.piece_type_to_name(captured_piece.piece_type, captured_piece.color)
        if captured_piece.color == chess.WHITE:
            self.captured_black.append(piece_name)
        else:
            self.captured_white.append(piece_name)
        self.check_captures()

    def update_captured_pieces(self, frame, captured_pieces):
        for widget in frame.winfo_children():
            widget.destroy()

        for piece in captured_pieces:
            image = self.board_images.get(piece)
            if image:
                img = image.resize((40, 40))
                img_tk = ImageTk.PhotoImage(img)
                label = tk.Label(frame, image=img_tk)
                label.pack(side=tk.TOP, pady=5)
                label.image = img_tk

    def check_captures(self):
        captured_white_value = sum([PIECE_VALUES[piece[1:]] for piece in self.captured_white])
        captured_black_value = sum([PIECE_VALUES[piece[1:]] for piece in self.captured_black])

        material_diff = captured_white_value - captured_black_value

        if material_diff > 0:
            self.material_label.config(text=f"Material: White +{material_diff}")
        elif material_diff < 0:
            self.material_label.config(text=f"Material: Black +{abs(material_diff)}")
        else:
            self.material_label.config(text="Material: Even")

        self.update_captured_pieces(self.captured_white_frame, self.captured_white)
        self.update_captured_pieces(self.captured_black_frame, self.captured_black)

    def update_move_history(self):
        self.move_history.config(state="normal")
        self.move_history.delete(1.0, tk.END)

        moves = list(self.board.move_stack)
        temp_board = chess.Board()

        for i in range(0, len(moves), 2):
            white = temp_board.san(moves[i])
            temp_board.push(moves[i])

            if i + 1 < len(moves):
                black = temp_board.san(moves[i + 1])
                temp_board.push(moves[i + 1])
            else:
                black = ""

            self.move_history.insert(tk.END, f"{(i // 2) + 1}. {white:6} {black:6}\n")

        self.move_history.see(tk.END)
        self.move_history.config(state="disabled")
        self.check_captures()

    def animate_move(self, move, steps=5, delay=30):
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
            x = from_col * self.square_size + dx * i + self.square_size // 2 + self.margin
            y = from_row * self.square_size + dy * i + self.square_size // 2 + self.margin
            self.canvas.create_image(x, y, image=img_tk)
            self.canvas.image = img_tk
            if i < steps:
                self.root.after(delay, step, i + 1)
            else:
                self.draw_board()

        step(0)

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
        self.draw_board()
        self.update_captured_pieces(self.captured_white_frame, self.captured_white)
        self.update_captured_pieces(self.captured_black_frame, self.captured_black)
        self.material_label.config(text="Material: Even")


def main():
    root = tk.Tk()
    game = ChessGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
