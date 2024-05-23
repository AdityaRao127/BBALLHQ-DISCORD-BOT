package GuessGame;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.Scanner;
import java.util.Stack;

public class GuessGame {

	private List<Player> players = new ArrayList<>();
	private GuessTracker guessedPlayers = new GuessTracker();

	private Player currentPlayer;
	private Map<String, Player> playerMap = new HashMap<>();

	private Stack<String> hintStack = new Stack<>();

	// Main method to start the game
	public static void main(String[] args) {
		GuessGame game = new GuessGame();
		game.play();
	}

	public GuessGame() {
		loadPlayers("players.txt");

	}

	// Method to load players from a file
	private void loadPlayers(String playerFile) {
		/***************************************************************************************
		 * Title: Java String trim() Method Author: W3Schools Date: May 16, 2024 Code
		 * version: N/A Availability: https://www.w3schools.com/java/java_try_catch.asp
		 * Usage: try and catch exceptions.
		 *
		 ***************************************************************************************/

		try {
			// scanner object to read the players.txt file
			Scanner scanner = new Scanner(new File(playerFile));
			// store all lines in a list
			List<String> lines = new ArrayList<>();
			while (scanner.hasNextLine()) {
				lines.add(scanner.nextLine());
			}
			scanner.close();

			// Use a for each loop to process each line. accessing elements, so easier to
			// use for each loop
			for (String line : lines) {
				String[] parts = line.split(",");
				/***************************************************************************************
				 * Title: Java String trim() Method Author: W3Schools Date: May 16, 2024 Code
				 * version: N/A Availability: https://www.w3schools.com/java/ref_string_trim.asp
				 * Usage: trim functions
				 ***************************************************************************************/

				if (parts.length == 4) {
					// trim line into four parts (name, team, position, conference)
					String name = parts[0].trim();
					String team = parts[1].trim();
					String position = parts[2].trim();
					String conference = parts[3].trim();
					Player player = new Player(name, team, position, conference);

					players.add(player); // add the player to the list of players
					playerMap.put(name, player); // store player by name
				}
			}
		} catch (FileNotFoundException e) {
			// error message if file not found
			System.out.println("Error");
		}
	}

	// system generates a random player for the user to guess from players.txt
	private Player getRandomPlayer() {
		Random r = new Random(); // object to generate random numbers using the random library
		Player player = null; // declaration of player variable

		while (player == null || guessedPlayers.contains(player)) { // find a player who has not been guessed. the game
																	// willl be run multiple times in a session so just
																	// make sure same player wont be selected in future
																	// rounds
			int index = r.nextInt(players.size()); // get random index from players.txt list of players
			player = players.get(index); // get player at that random index
		}

		guessedPlayers.addPlayer(player); // add selected player to guessedPlayers queue
		return player; // returns random player
	}

	private void hints(Player player) {

		hintStack.clear(); // clear previous hints from the stack
		hintStack.push("Team: " + player.getTeam()); // first hint is team, given by use the getter function for the
														// player object.
		hintStack.push("Position: " + player.getPosition()); // second hint is position, given by use the getter
																// function for the player object.
		hintStack.push("Conference: " + player.getConference());// third hint is position, given by use the getter
																// function for the player object.
	}

	// Main game loop
	public void play() {
		Scanner s = new Scanner(System.in); // define scanner at top and not in game loop
		currentPlayer = getRandomPlayer(); // Select a random player
		boolean playAgain = true; // new game

		while (playAgain) { // keep playing game if user wants to

			currentPlayer = getRandomPlayer();

			// Check if a player was successfully selected
			if (currentPlayer == null) {
				System.out.println("Failed to start the game due to no players being loaded.\n");
				return;
			}

			hints(currentPlayer); // Prepare hints for the player

			int attempts = 3; // how many guesses the user has.

			System.out.println("Welcome to the NBA Guessing game!");
			System.out.println("You have " + attempts + " attempts to guess the player.\n");

			// Loop to handle player guesses
			while (attempts > 0) {
				System.out.println("Hint-> " + hintStack.pop()); // print out a hint from the topmost element of stack.
																	// referenced Zybooks section 8.1

				System.out.print("Enter your guess: ");
				String guess = s.nextLine().trim(); // remove trailing whitespace characters

				if (guess.equalsIgnoreCase(currentPlayer.getName())) { // ignore upper vs lower case, and see if user
																		// guess
																		// matches the answer.
					System.out.println("Congratulations! You guessed the player correctly.\n");
					break; // end game
				} else {
					attempts--; // decrement attempts
					if (attempts == 0) {
						System.out.println("Game over! The correct player was: " + currentPlayer.getName());
					} else {
						System.out.println("Incorrect guess. Attempts remaining: " + attempts + "\n"); // new line, for
																										// spacing
					}
				}
			}

			// Ask the player if they want to play again
			System.out.print("\nDo you want to play again? (yes/no): ");
			String newGame = s.nextLine().trim().toLowerCase();
			if (!(newGame.equals("yes"))) {
				playAgain = false;
			}

		}
		s.close(); // close scanner
		System.out.println("\n\nGoodbye!");

	}

}