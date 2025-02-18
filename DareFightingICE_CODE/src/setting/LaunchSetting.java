package setting;

import enumerate.BackgroundType;

/**
 * キャラクターの最大HPや試合の繰り返し回数など、試合を行う際に必要な設定を扱うクラス．
 */
public final class LaunchSetting {

	public final static int LIGHTWEIGHT_MODE = 0;
	public final static int HEADLESS_MODE = 1;
	public final static int STANDARD_MODE = 2;
	
	/**
	 * P1,P2の最大HPを格納する配列．
	 */
	public static int[] maxHp = { 400, 400 };

	/**
	 * P1,P2の最大エネルギーを格納する配列．
	 */
	public static int[] maxEnergy = { 300, 300 };

	/**
	 * P1,P2のAI名を格納する配列．<br>
	 * キーボードの場合は"Keyboard"が格納される．
	 */
	public static String[] aiNames = { "KeyBoard", "KeyBoard" };

	/**
	 * P1,P2のキャラクター名．
	 */
	public static String[] characterNames = { "ZEN", "ZEN" };
	
	public static String soundName = "Default";

	/**
	 * 利用するデバイスタイプ．<br>
	 * {@code 0} if the device type is keyboard，or {@code 1} if AI.
	 */
	public static char[] deviceTypes = { 0, 0 };

	/**
	 * 試合を繰り返して行う回数．
	 */
	public static int repeatNumber = 1;

	/**
	 * 画素を反転させるプレイヤーの番号．
	 */
	public static int invertedPlayer = 0;

	/**
	 * 背景の種類．
	 */
	public static BackgroundType backgroundType = BackgroundType.IMAGE;

	/**
	 * リプレイデータの名前．
	 */
	public static String replayName = "None";

	/**
	 * 試合の繰り返し回数のカウンタ．
	 */
	public static int repeatedCount = 0;
	
	public static int processingMode = STANDARD_MODE;

	/**
	 * AI's visual data is disabled or not
	 */
	public static boolean[] noVisual = {false, false};
	
	public static boolean[] nonDelay = {false, false};
	
	public static int serverPort = 31415;
	
	public static boolean isExpectedProcessingMode(int expectedProcessingMode) {
		return processingMode >= expectedProcessingMode;
	}
	
}
