<html>
<head>
	<style type="text/css">
		body
		{
			background  : white;
			line-height : 1.6em;
  			font-family : "Lucida Sans Unicode", "Lucida Grande", Sans-Serif;
			text-align  : center;
		}

		h1
		{
			font-size   : 24px;
		}

		caption
		{
			color            : white;
			background-color : #038;
			font-size        : 12px;
			font-weight      : bold;			
		}

		tbody
		{
			color  : blue;
		}

		tfoot
		{
			color  : red;
		}

		table
		{
			margin-left     : auto;
			margin-right    : auto;
   			border-collapse : collapse;
			font-size       : 12px;
			background      : #fff;
		}

		th
		{
			font-size     : 14px;
			font-weight   : normal;
			color         : #039;
			padding       : 10px 8px;
			border-bottom : 2px solid #6678b1;
		}

		td
		{
			border-bottom : 1px solid #ccc;
			color         : #669;
			padding       : 6px 8px;
			text-align    : center;
		}

		td.contents
		{
			text-align : left;
		}

		div.summary
		{
			height : 16px;
			overflow : hidden;
		}
		div.full
		{
		}

		tbody tr:hover td
		{
			color: #009;
		}

		table.filter
		{
			text-align : center;
		}

		table.results
		{
			width : 95%;
		}

		a:link
		{
			color:#000;
		}
		a:visited
		{
			color:#039;
		}
		a:hover
		{
			color:#00F;
		}
		a:active
		{
			color:#0000FF;
		}
	</style>

	<script type="text/javascript">
		function toggleDiv(div)
		{
			if (div.className == "summary")
			{
				div.setAttribute("class", "full");
				div.setAttribute("className", "full");
 			}
			else
			{
				div.setAttribute("class", "summary");
				div.setAttribute("className", "summary");
			}
		}
	</script>

</head>

<body>

<?php

//set the timezone, otherwise mktime and friends have a hissy
date_default_timezone_set('UTC');

//set up some options, either from the passed in values, or if missing, their default values
$databaseFilename = '/var/www/monkeybot/monkey.db';
$search = isset($_GET['search']) ? $_GET['search'] : '';
$new = isset($_GET['new']) ? $_GET['new'] : '=0';
$added = isset($_GET['added']) ? $_GET['added'] : 'All';
$action = isset($_GET['action']) ? $_GET['action'] : 'All';
$remove = isset($_GET['remove']) ? $_GET['remove'] : '';
unset($_GET['remove']); //we don't want this variable to persist past this one-time use
$thisPage = createQueryString();

//set up some filter options
$addedOptions = array('All', 'Today', 'Yesterday');
$newOptions = array('=0', '<5', '<10', '<100', 'All');

//some of the HTML generated, ick
$filterTableHeader = '<table class="filter">' .
                         '<caption>Filter</caption>' .
                         '<thead><tr>' .
                             '<th>Added</th><th>Category</th><th>ShowCount</th><th>Search</th><th></th>' .
                         '</tr></thead>' .
                         '<tbody>';
$filterTableFooter =     '</tbody>' .
                     '</table>';                        

$resultTableHeader = '<table class="results">' .
					     '<caption>Results</caption>' .
					     '<thead><tr>' .
					         '<th>ID</th><th>Added</th><th>Category</th><th>Contents</th><th>Delete</th><th>ShowCount</th>' .
					     '</tr></thead>' .
					     '<tbody>';
$resultTableFooter =     '</tbody>' .
                     '</table>';


function createQueryString($array = array(), $kvSep = '=', $varSep = '&') 
{
	$get = array_merge($_GET, $array);
	$getVars = array();
	foreach ($get as $key => $value) 
	{
		if (is_string($key))
			$getVars[] = implode($kvSep, array($key, $value));
	}
	return implode($varSep, $getVars);
}

function addWhere($currentWhere, $newFilter)
{
	if ($currentWhere == '')
		$currentWhere = ' WHERE ';
	else
		$currentWhere = $currentWhere . ' AND ';
	$currentWhere = $currentWhere . $newFilter;
	return $currentWhere;
}

function getUpdateShowCountQuery($shownIds)
{
	$sql = 'UPDATE message SET showCount=showCount+1 WHERE id IN(';
	foreach ($shownIds as $item)
		$sql = $sql . $item['id'] . ',';
	$sql = rtrim($sql, ',');
	$sql = $sql . ')';
	return $sql;
}

function removeMessage($db, $id)
{
	if ($id == '')
		return;

	$sql = "UPDATE message SET deleted=deleted+1 WHERE message.id=$id";
	$db->exec($sql);
	//$sql = "DELETE FROM messages WHERE messages.rowid IN (SELECT messageId FROM message WHERE message.id=$id);";
	//$db->exec($sql);
	//$sql = "DELETE FROM url WHERE messageId=$id;";
	//$db->exec($sql);
	//$sql = "DELETE FROM message WHERE id=$id;";
	//$db->exec($sql);
}

function openDatabase($Filename)
{
	try
	{
		$db = new PDO("sqlite:$Filename");
		$db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_WARNING);
		return $db;	
	}	
	catch(PDOException $e)
	{
		die('Exception : '.$e->getMessage());
	}
	return null;
}

function getCategories($Database)
{
	$result = $Database->query('SELECT DISTINCT action FROM message');
	if (!$result)
	{
		echo 'Could not get categories: ';
		print_r($Database->errorInfo());
		die();
	}
	return $result;
}

//And now ladies and gentlemen, procedural hell...

//open the database
$db = openDatabase($databaseFilename);
//delete a message if one has been toggled for removal
removeMessage($db, $remove);

//this array is filled with the id's of every message display in this instance of this page.
//at the end, the showCount columns for these messages are updated to reflect they have been shown.
//(this is handy for marking new items are being viewed, and for seeing which messages are looked
// at the most, "favourites" if you will.)
$shownIds = array();

//display the filter option column titles
echo '<form action="monkeyview.php" method="get">';
echo $filterTableHeader;

//"added" filter box
echo '<tr>';
echo '<td><select name="added">';
foreach ($addedOptions as $option)
{
	$selected = ($option == $added) ? ' selected' : '';
	echo '<option' . $selected . '>' . $option . '</option>';
}
echo '</select></td>';

//"action" filter box, basically the category.
echo '<td><select name="action">';
echo ' <option>All</option>';
$result = getCategories($db);
foreach ($result as $row)
{
	$selected = ($row['action'] == $action) ? ' selected' : '';
	echo '<option' . $selected . '>' . $row['action'] . '</option>';
}
echo '</select></td>';

//"new" filter box, let's you limit by how many times a message has appeared before
echo '<td><select name="new">';
foreach ($newOptions as $option)
{
	$selected = ($option == $new) ? ' selected' : '';
	echo '<option' . $selected . '>' . $option . '</option>';
}
echo '</select></td>';
echo '<td><input type="text" name="search" value="' . $search . '"></td>';
echo '<td><input type="submit" value="Apply"></td>';
echo '</tr>';
echo $filterTableFooter;
echo '</form><br>';

//build the where filter, based on the options above
$where = '';
if ($added !== 'All')
{
	$start = getdate();
	$start = mktime(0, 0, 0, $start['mon'], $start['mday'], $start['year']);
	if ($added == 'Yesterday')
		$start -= (60 * 60 * 24);
	$end = $start + (60 * 60 * 24);
	$where = addWhere($where, "(message.added>=$start AND message.added<$end)");
}
if ($action !== 'All')
{
	$where = addWhere($where, '(message.action=\'' . $action . '\')');
}
if ($new !== 'All')
{
	$where = addWhere($where, '(message.showCount' . $new . ')');
}
if ($search !== '')
{
	$where = addWhere($where, '(messages.contents MATCH \'' . $search . '\')');
}
$where = addWhere($where, '(message.deleted=0)');

//display the contents
$sql = 'SELECT messages.contents, message.action, message.id, message.added, message.showCount, message.readCount FROM messages INNER JOIN message on messages.rowId=message.messageId ' . $where . ' ORDER BY message.added DESC';
$result = $db->query($sql);

$index = 0;
foreach ($result as $row)
{
	//I don't think there's a way to get how many rows are returned from a SQLite query, and I'm too
	//lazy to find out, so simply only write out the table if we have data to output
	if (!$index)
		echo $resultTableHeader;

	$shownIds[$index]['showCount'] = $row['showCount'];
	$shownIds[$index]['id'] = $row['id'];
	$index++;

	$addDate = gmdate("Y-m-d", $row['added']);
	$addTime = gmdate("H:i:s", $row['added']);
	echo '<tr>';
	echo '<td>' . $row['id'] . '</td>';
	echo "<td title='$addTime'>$addDate</td>";
	echo '<td>' . $row['action'] . '</td>';
	$divName = "div$index";
	echo '<td class="contents"><div class="full" onclick="toggleDiv(this);">';
		echo $row['contents'];
		$urls = $db->query('SELECT * FROM url WHERE messageId='. $row['id']);
		$urlIndex = 0;
		foreach ($urls as $url)
		{
			$link = rtrim($url['url'], ',.');
			if (substr($link, 0, 7) !== 'http://')
				$link = 'http://' . $link;

			if ($urlIndex == 0)
				echo '<br>';

			echo '<a href="' . $link . '">Url #' . ($urlIndex+1) . '</a> &nbsp;';
			$urlIndex++;
		}
	echo '</div></td>';
	echo '<td><a href="monkeyview.php?remove=' . $row['id'] . '&' . $thisPage . '">nuke</a>' . '</td>';
	echo '<td>' . $row['showCount'] . '</td>';
	echo "</tr>\n";
}

if ($index)
{
	echo $resultTableFooter;
	//update the show counts of the items on screen
	$result = $db->exec(getUpdateShowCountQuery($shownIds));
}
else
{
	echo "<h1>No results returned.</h1>";
}

// close the database connection
$db = NULL;

?>

</body>
</html>
