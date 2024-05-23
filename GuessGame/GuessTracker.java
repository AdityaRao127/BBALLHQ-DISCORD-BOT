package GuessGame;
import java.util.*;

public class GuessTracker {
	private Queue<Player> queue; // create a queue

	// default contructor, for the GuessTracker class
	public GuessTracker() {
		queue = new LinkedList<>(); // queue is set as a linkedList
	}

	// add a player to end of the queue
	public void addPlayer(Player player) {
		// taken from table 28.5.1 common queue methods
		queue.add(player);
	}

	public Player removePlayer() {
		// taken from table 28.5.1 common queue methods
		return queue.poll();

		// removes and returns the player at the front of the queue.returns null if
		// empty
	}

	// check if player exists in queue
	public boolean contains(Player player) {
		return queue.contains(player);
	}
}