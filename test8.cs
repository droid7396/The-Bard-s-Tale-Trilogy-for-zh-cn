using System; using System.Text.RegularExpressions; class P { static void Main() { Console.WriteLine(Regex.IsMatch("Press <color=#ffff22>{0}</color> to continue...", @"\{\d+\}")); } }
