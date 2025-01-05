use rschess::{Board, img};
use rschess::Color;

fn main() {
    let board = Board::default();
    println!("{}", board.pretty_print(Color::White));

    let image = img::position_to_image(
        board.position(),                        // the position
        img::PositionImageProperties::default(), // image properties
        board.side_to_move(),                    // perspective
    );
    match image
    {
        Ok(img) => {
            match img.save("test.png")
            {
                Ok(t) => println!("Image saved."),
                Err(err)  => println!("{}", err),
            }
        },
        Err(err) => println!("{}", err),
    }

    // match pgn
    // {
    //     Ok(pgn) => {
    //          let board = pgn.board();
    //     },
    //     Err(error) => { println!("{}", error); }
    // }
}
